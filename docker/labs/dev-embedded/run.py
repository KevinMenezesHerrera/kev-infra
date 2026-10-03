#!/usr/bin/env python3
"""dev-embedded integration checks; host dependencies: Docker CLI and Python stdlib."""
import argparse
import json
import os
from pathlib import Path
import shutil
import shlex
import subprocess
import tempfile
import uuid

REPO = Path(__file__).resolve().parents[3]
DOCKER = ['docker', '--host', 'unix:///run/user/1000/docker.sock']
TOKEN = 'phase7b-' + uuid.uuid4().hex[:12]
containers = set()
scratch = None
daemon_used = False


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
    global scratch, daemon_used
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
    compose = DOCKER + ['compose', '-p', TOKEN, '-f', str(REPO / 'docker/tools/embedded/compose.yaml'),
                        '--profile', '*']
    cfg = json.loads(call(compose + ['config', '--format', 'json'], capture=True, env=env))
    validate(cfg, project)
    if args.config_only:
        return
    daemon_used = True
    print('RUN: ' + TOKEN, flush=True)
    if args.build:
        call(compose + ['build', 'sandbox'], env=env)
        passed('build dev-embedded')
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

    for path in (Path(__file__).resolve().parent / 'fixture').iterdir():
        shutil.copyfile(path, project / path.name)
    inspection = r"""
arm-none-eabi-readelf -h -S -l -A "$out/firmware.elf" > "$out/readelf.txt"
cat "$out/readelf.txt"
grep -q 'Machine:.*ARM' "$out/readelf.txt"
grep -q 'Class:.*ELF32' "$out/readelf.txt"
grep -q 'Type:.*EXEC' "$out/readelf.txt"
grep -q 'Tag_CPU_arch: v7' "$out/readelf.txt"
grep -q 'Tag_CPU_arch_profile: Microcontroller' "$out/readelf.txt"
for section in .vectors .text .data .bss .debug_info; do
  grep -Fq "$section" "$out/readelf.txt"
done
grep -q LOAD "$out/readelf.txt"
grep -q '.bss.*NOBITS.*20000004' "$out/readelf.txt"
grep -q '.data.*PROGBITS.*20000000' "$out/readelf.txt"
arm-none-eabi-nm -n "$out/firmware.elf" > "$out/nm.txt"
cat "$out/nm.txt"
for symbol in Reset_Handler main counter seed _stack_top; do
  grep -q " $symbol$" "$out/nm.txt"
done
entry=$(arm-none-eabi-readelf -h "$out/firmware.elf" | awk '/Entry point/ {print $4}')
reset=$(awk '/ T Reset_Handler$/ {print $1}' "$out/nm.txt")
test "$((entry & ~1))" = "$((0x$reset))"
arm-none-eabi-objdump -d "$out/firmware.elf" > "$out/disassembly.txt"
grep -q '<main>' "$out/disassembly.txt"
arm-none-eabi-size "$out/firmware.elf"
test "$(wc -c < "$out/firmware.bin")" = 108
set -- $(od -An -tu4 -N8 "$out/firmware.bin")
test "$1" = "$((0x20005000))"
test "$2" = "$((entry))"
arm-none-eabi-objcopy -I ihex -O binary "$out/firmware.hex" "$out/from-hex.bin"
cmp "$out/firmware.bin" "$out/from-hex.bin"
for artifact in main.o startup.o firmware.elf firmware.bin firmware.hex firmware.map; do
  test -s "$out/$artifact"
done
"""
    mode('edit', """
for tool in arm-none-eabi-gcc arm-none-eabi-readelf arm-none-eabi-objcopy make; do
  "$tool" --version
done
dpkg-query -W gcc-arm-none-eabi binutils-arm-none-eabi make
test "$(id -u):$(id -g)" = 0:0
cat /proc/self/uid_map /proc/self/gid_map
make -j1
out=build
""" + inspection)
    # Independent container, same source and output paths; preserve debug flags.
    first = {p.name: p.read_bytes() for p in (project / 'build').iterdir()}
    shutil.rmtree(project / 'build')
    mode('edit', 'make -j1; out=build\n' + inspection)
    import hashlib
    for name in ('main.o', 'startup.o', 'firmware.elf', 'firmware.bin', 'firmware.hex', 'firmware.map'):
        before = hashlib.sha256(first[name]).hexdigest()
        after = hashlib.sha256((project / 'build' / name).read_bytes()).hexdigest()
        print(f'HASH same-path {name}: {before} {after} equal={before == after}', flush=True)
    for path in project.rglob('*'):
        require((path.stat().st_uid, path.stat().st_gid) == (1000, 1000), 'ownership: ' + str(path))
    passed('cross-compilation, ELF structure, entry/symbols, BIN/HEX roundtrip, ownership, recreation')
    (project / 'build' / 'host-removable').write_text('host edit')
    (project / 'build' / 'host-removable').unlink()
    source = project / 'main.c'
    source.write_text(source.read_text().replace('seed = 7', 'seed = 9'))
    old_bin = (project / 'build/firmware.bin').read_bytes()
    mode('edit', 'make -j1; out=build\n' + inspection)
    require((project / 'build/firmware.bin').read_bytes() != old_bin, 'host source edit did not change BIN')
    passed('host edits/removes artifacts; edited source compiled in recreated container')
    snapshot = {str(p.relative_to(project)): p.read_bytes() for p in project.rglob('*') if p.is_file()}
    mode('test', r"""
if touch /workspace/forbidden 2>/tmp/write-error; then exit 1; fi
grep -qi 'read-only file system' /tmp/write-error
make -j1 OUT=/tmp/build
out=/tmp/build
""" + inspection + r"""
for artifact in firmware.elf firmware.bin firmware.hex firmware.map; do
  sha256sum "/workspace/build/$artifact" "/tmp/build/$artifact"
  if cmp -s "/workspace/build/$artifact" "/tmp/build/$artifact"; then
    echo "PATH-COMPARE $artifact equal"
  else
    echo "PATH-COMPARE $artifact different"
  fi
done
arm-none-eabi-readelf --debug-dump=info /workspace/build/firmware.elf > /tmp/debug-edit
arm-none-eabi-readelf --debug-dump=info /tmp/build/firmware.elf > /tmp/debug-test
diff -u /tmp/debug-edit /tmp/debug-test || test "$?" = 1
diff -u /workspace/build/firmware.map /tmp/build/firmware.map || test "$?" = 1
awk '$2 == "/tmp" && $4 ~ /(^|,)noexec(,|$)/ { found=1 } END { if (!found) exit 1 }' /proc/mounts
""")
    require(snapshot == {str(p.relative_to(project)): p.read_bytes() for p in project.rglob('*') if p.is_file()},
            'TEST modified project')
    passed('TEST read-only; temporary build and inspection; noexec; path comparison measured')
    sandbox_source = '\n'.join(
        'printf %s ' + shlex.quote(path.read_text()) + ' > ' + shlex.quote('/workspace/' + path.name)
        for path in (Path(__file__).resolve().parent / 'fixture').iterdir())
    mode('sandbox', 'test ! -e /workspace/main.c\n' + sandbox_source
         + '\nmake -j1; out=build\n' + inspection + '\n' + """

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
""")
    mode('sandbox', 'test ! -e /workspace/main.c; test ! -e /workspace/transient; test ! -e /tmp/transient')
    passed('SANDBOX isolation, rootfs, capabilities, no-new-privileges, network, tmpfs recreation, cgroups')
    require((project / 'main.c').is_file(), 'container removal lost host source')
    passed('all dev-embedded experiments; no hardware execution')


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
    require(not docker('container', 'ls', '-a', '--filter',
                       'label=com.docker.compose.project=' + TOKEN,
                       '--format', '{{.ID}}', capture=True) if daemon_used else True,
            'owned containers remain')
    passed('cleanup: only resources created by this run; no volumes or networks created')


if __name__ == '__main__':
    try:
        main()
    finally:
        cleanup()
