#!/usr/bin/env python3
"""dev-c integration checks; host dependencies: Docker CLI and Python stdlib."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import uuid

REPO = Path(__file__).resolve().parents[3]
DOCKER = ['docker', '--host', 'unix:///run/user/1000/docker.sock']
TOKEN = 'phase7a-' + uuid.uuid4().hex[:12]
containers = set()
scratch = None


def call(args, *, capture=False, check=True, env=None):
    result = subprocess.run(args, text=True, check=check, env=env,
                            stdout=subprocess.PIPE if capture else None)
    return result.stdout.strip() if capture else result.returncode


def docker(*args, **kwargs):
    return call(DOCKER + list(args), **kwargs)


def require(condition, message):
    if not condition:
        raise RuntimeError('FAIL: ' + message)


def passed(message):
    print('PASS: ' + message, flush=True)


def inspect(name):
    return json.loads(docker('container', 'inspect', name, capture=True))[0]


def remove_container(name):
    require(name in containers, 'container not registered by this run')
    info = inspect(name)
    require(info['Config']['Labels'].get('com.docker.compose.project') == TOKEN,
            'container ownership label mismatch')
    docker('container', 'rm', '-f', info['Id'])
    containers.remove(name)


def validate(cfg, project):
    require(set(cfg['services']) == {'edit', 'test', 'sandbox'}, 'expected modes')
    require(not cfg.get('volumes') and not cfg.get('networks'), 'persistent resources')
    for name, service in cfg['services'].items():
        require(service['user'] == '0:0' and service['read_only'], name + ': identity/rootfs')
        require(service['network_mode'] == 'none', name + ': network')
        require(int(service['mem_limit']) == 268435456 and float(service['cpus']) == 0.5
                and service['pids_limit'] == 64, name + ': limits')
        require(service['cap_drop'] == ['ALL'] and not service.get('cap_add'), name + ': caps')
        require(service['security_opt'] == ['no-new-privileges:true'], name + ': security options')
        for key in ('privileged', 'devices', 'device_cgroup_rules', 'ports', 'secrets',
                    'configs', 'volumes_from', 'pid', 'ipc', 'userns_mode'):
            require(not service.get(key), name + ': unexpected ' + key)
        expected_tmpfs = ['/tmp:rw,nosuid,nodev,size=64m,mode=1777']
        if name == 'sandbox':
            expected_tmpfs += ['/workspace:rw,nosuid,nodev,size=64m,mode=0755']
            require(not service.get('volumes'), 'sandbox persistent mount')
        else:
            mounts = service['volumes']
            require(len(mounts) == 1, name + ': mount count')
            mount = mounts[0]
            require(mount['type'] == 'bind' and mount['source'] == str(project)
                    and mount['target'] == '/workspace', name + ': project mount')
            require(bool(mount.get('read_only')) == (name == 'test'), name + ': mount access')
            require(mount['bind']['create_host_path'] is False, name + ': implicit host path')
        require(service['tmpfs'] == expected_tmpfs, name + ': tmpfs')
    passed('Compose config and structural safety')


def main():
    global scratch
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', action='store_true',
                        help='explicitly allow build; may download pinned base/packages')
    parser.add_argument('--config-only', action='store_true', help='validate Compose without daemon')
    args = parser.parse_args()
    # Avoid environment overrides of the deliberately fixed local endpoint.
    for key in ('DOCKER_HOST', 'DOCKER_CONTEXT', 'DOCKER_TLS', 'DOCKER_TLS_VERIFY', 'DOCKER_CERT_PATH'):
        os.environ.pop(key, None)
    if not args.config_only:
        call([str(REPO / 'scripts/check-infra')])
        require(os.getuid() == os.getgid() == 1000, 'expected host identity 1000:1000')
    scratch = Path(tempfile.mkdtemp(prefix='scratch.', dir=Path(__file__).resolve().parent))
    project = scratch / 'project'
    project.mkdir()
    env = dict(os.environ, DEV_WORKSPACE=str(project))
    compose = DOCKER + ['compose', '-p', TOKEN, '-f', str(REPO / 'docker/tools/c/compose.yaml'),
                        '--profile', '*']
    cfg = json.loads(call(compose + ['config', '--format', 'json'], capture=True, env=env))
    validate(cfg, project)
    if args.config_only:
        return
    print('RUN: ' + TOKEN, flush=True)
    if args.build:
        call(compose + ['build', 'sandbox'], env=env)
        passed('build dev-c')
    else:
        docker('image', 'inspect', cfg['services']['sandbox']['image'], capture=True)
        print('BUILD: skipped (use --build after network approval)', flush=True)

    def mode(name, code):
        cname = TOKEN + '-' + uuid.uuid4().hex[:8]
        require(cname not in docker('container', 'ls', '-a', '--format', '{{.Names}}',
                                    capture=True).splitlines(), 'existing container name')
        # Register intent before creation so ordinary command failures can be cleaned.
        containers.add(cname)
        result = call(compose + ['run', '--pull', 'never', '--name', cname,
                                 '--no-deps', '-T', name, 'sh', '-eu', '-c', code],
                      check=False, env=env)
        info = inspect(cname)
        host = info['HostConfig']
        require(info['Config']['User'] == '0:0', 'runtime identity')
        require(host['ReadonlyRootfs'] and not host['Privileged'], 'runtime rootfs/privilege')
        require(host['CapDrop'] == ['ALL'] and not host['CapAdd'], 'runtime caps')
        require(host['SecurityOpt'] == ['no-new-privileges:true'], 'runtime security options')
        require(host['NetworkMode'] == 'none' and not host['Devices'], 'runtime network/devices')
        require(host['Memory'] == 268435456 and host['NanoCpus'] == 500000000
                and host['PidsLimit'] == 64, 'runtime limits')
        mounts = [m for m in info['Mounts'] if m['Type'] != 'tmpfs']
        if name == 'sandbox':
            require(not mounts, 'sandbox host data exposure')
        else:
            require(len(mounts) == 1 and mounts[0]['Type'] == 'bind'
                    and mounts[0]['Source'] == str(project)
                    and mounts[0]['Destination'] == '/workspace'
                    and mounts[0]['RW'] == (name == 'edit'), 'runtime bind')
        require(set(host['Tmpfs']) == ({'/tmp', '/workspace'} if name == 'sandbox' else {'/tmp'}),
                'runtime tmpfs')
        remove_container(cname)
        require(result == 0 and info['State']['ExitCode'] == 0, name + ': command failed')

    source = '#include <stdio.h>\nint main(void) { puts("host-v1"); return 0; }\n'
    (project / 'main.c').write_text(source)
    (project / 'Makefile').write_text('hello-make: main.c\n\t$(CC) -Wall -Wextra -Werror -g -O0 $< -o $@\n')
    (project / 'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.16)\n'
                                         'project(dev_c_lab LANGUAGES C)\nadd_executable(hello main.c)\n')
    mode('edit', '''
for tool in gcc make cmake ninja pkg-config gdb; do "$tool" --version; done
test "$(id -u):$(id -g)" = 0:0
cat /proc/self/uid_map /proc/self/gid_map
gcc -Wall -Wextra -Werror -g -O0 main.c -o hello
test "$(./hello)" = host-v1
make -j1
test "$(./hello-make)" = host-v1
cmake -S . -B build-make -G 'Unix Makefiles' -DCMAKE_BUILD_TYPE=Debug
cmake --build build-make --parallel 1
test "$(./build-make/hello)" = host-v1
cmake -S . -B build-ninja -G Ninja -DCMAKE_BUILD_TYPE=Debug
cmake --build build-ninja --parallel 1
test "$(./build-ninja/hello)" = host-v1
gdb -nx -nh -batch -iex 'set auto-load off' ./hello \\
  -ex 'info address main' -ex 'break main' -ex 'info breakpoints' > /tmp/gdb.txt
cat /tmp/gdb.txt
grep -q 'Symbol "main"' /tmp/gdb.txt
grep -q 'main.c' /tmp/gdb.txt
''')
    passed('toolchain versions; GCC, Make, CMake/Make, CMake/Ninja; GDB symbols/breakpoint')
    artifacts = list(project.rglob('*'))
    for path in artifacts:
        require((path.stat().st_uid, path.stat().st_gid) == (1000, 1000), 'ownership: ' + str(path))
    print(f'OWNERSHIP: {len(artifacts)} entries, all 1000:1000', flush=True)
    (project / 'hello').write_bytes(b'host can replace generated binary\n')
    (project / 'hello').unlink()
    (project / 'main.c').write_text(source.replace('host-v1', 'host-v2'))
    mode('edit', '''
test ! -e hello
gcc -g -O0 main.c -o hello
test "$(./hello)" = host-v2
test "$(./build-ninja/hello)" = host-v1
''')
    require((project / 'main.c').read_text() == source.replace('host-v1', 'host-v2'), 'source preserved')
    passed('host edits/removes artifacts; source edits reach recreated container; persistence')
    mode('test', '''
test "$(./hello)" = host-v2
if touch /workspace/forbidden 2>/tmp/write-error; then exit 1; fi
cat /tmp/write-error
grep -qi 'read-only file system' /tmp/write-error
cmake -S /workspace -B /tmp/build -G Ninja
cmake --build /tmp/build --parallel 1
test -s /tmp/build/hello
# Docker's tmpfs is noexec by default. Verify that boundary rather than
# changing mount flags to execute newly compiled output in TEST.
awk '$2 == "/tmp" && $4 ~ /(^|,)noexec(,|$)/ { found=1 } END { if (!found) exit 1 }' /proc/mounts
if /tmp/build/hello 2>/tmp/exec-error; then exit 1; fi
cat /tmp/exec-error
grep -qi 'permission denied' /tmp/exec-error
''')
    require(not (project / 'forbidden').exists(), 'TEST modified project')
    passed('TEST rejects writes; out-of-tree CMake build succeeds; tmpfs noexec enforced')
    mode('sandbox', '''
test ! -e /workspace/main.c
test ! -e /var/run/docker.sock
test ! -e /run/user/1000/docker.sock
touch /workspace/transient /tmp/transient
for mountpoint in /tmp /workspace; do
  awk -v target="$mountpoint" '$2 == target && $4 ~ /(^|,)noexec(,|$)/ { found=1 } END { if (!found) exit 1 }' /proc/mounts
done
if touch /forbidden 2>/tmp/root-error; then exit 1; fi
grep -qi 'read-only file system' /tmp/root-error
awk '/^CapEff:/ { if ($2 != "0000000000000000") exit 1; found=1 } END { if (!found) exit 1 }' /proc/self/status
awk '/^NoNewPrivs:/ { if ($2 != 1) exit 1; found=1 } END { if (!found) exit 1 }' /proc/self/status
test "$(ls /sys/class/net)" = lo
test "$(cat /sys/fs/cgroup/memory.max)" = 268435456
awk '{ if ($1 / $2 != 0.5) exit 1 }' /sys/fs/cgroup/cpu.max
test "$(cat /sys/fs/cgroup/pids.max)" = 64
for resource in memory.max cpu.max pids.max; do
  printf '%s: ' "$resource"; cat "/sys/fs/cgroup/$resource"
done
''')
    mode('sandbox', 'test ! -e /workspace/transient; test ! -e /tmp/transient')
    passed('SANDBOX isolation, rootfs, capabilities, no-new-privileges, network, tmpfs recreation, cgroups')
    require((project / 'main.c').is_file(), 'container removal lost host source')
    passed('all dev-c experiments')


def cleanup():
    # Never remove a resource solely because its name matches a prefix.
    existing = set()
    if containers:
        existing = set(docker('container', 'ls', '-a', '--format', '{{.Names}}', capture=True).splitlines())
    for name in list(containers):
        if name in existing:
            remove_container(name)
        else:
            containers.remove(name)
    if scratch is not None:
        require(scratch.parent == Path(__file__).resolve().parent
                and scratch.name.startswith('scratch.'), 'unsafe scratch cleanup')
        shutil.rmtree(scratch)
    passed('cleanup: only resources created by this run; no volumes or networks created')


if __name__ == '__main__':
    try:
        main()
    finally:
        cleanup()
