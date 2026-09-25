#!/usr/bin/env python3
"""Controlled integration lab; uses only Python stdlib on the control plane."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import uuid

REPO = Path(__file__).resolve().parents[3]
DOCKER = ['docker', '--host', 'unix:///run/user/1000/docker.sock']
IMAGE = 'kev-infra/dev-python:3.13.7'
TOKEN = 'phase6-' + uuid.uuid4().hex[:12]
LABEL = 'kev-infra.lab=' + TOKEN
containers = set()
volume = None
scratch = None


def call(args, *, capture=False, check=True, env=None):
    result = subprocess.run(args, text=True, stdout=subprocess.PIPE if capture else None,
                            check=check, env=env)
    return result.stdout.strip() if capture else result.returncode


def docker(*args, **kwargs):
    return call(DOCKER + list(args), **kwargs)


def require(condition, message):
    if not condition:
        raise RuntimeError('FAIL: ' + message)


def passed(message):
    print('PASS: ' + message, flush=True)


def inspect(kind, name):
    return json.loads(docker(kind, 'inspect', name, capture=True))[0]


def remove_container(cid):
    require(cid in containers, 'container not created by this run')
    labels = inspect('container', cid)['Config']['Labels']
    require(labels.get('kev-infra.lab') == TOKEN
            or labels.get('com.docker.compose.project') == TOKEN, 'container label mismatch')
    docker('container', 'rm', '-f', cid)
    containers.remove(cid)


def run_image(code, mounts=(), *, writable=False):
    args = ['container', 'create', '--label', LABEL, '--network', 'none',
            '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
            '--memory', '256m', '--cpus', '0.5', '--pids-limit', '64']
    if not writable:
        args += ['--read-only']
    for mount in mounts:
        args += ['--mount', mount]
    cid = docker(*args, IMAGE, 'python', '-c', code, capture=True)
    containers.add(cid)
    print('CREATED container ' + cid, flush=True)
    docker('start', '-a', cid)
    require(inspect('container', cid)['State']['ExitCode'] == 0, 'Python lab failed')
    remove_container(cid)


def validate(config):
    for name, service in config['services'].items():
        require(not service.get('privileged'), name + ': privileged')
        require(not service.get('devices'), name + ': devices')
        for mount in service.get('volumes', []):
            source = mount.get('source', '')
            target = mount.get('target', '')
            require('docker.sock' not in source and 'docker.sock' not in target,
                    name + ': socket mount')
            if mount['type'] == 'bind':
                resolved = str(Path(source).resolve())
                require(resolved not in ('/', '/home', str(Path.home())), name + ': broad bind')
    passed('Compose structured safety checks')


def main():
    global volume, scratch
    # Standalone entry is as defensive as the shell wrapper.
    call([str(REPO / 'docker/labs/rootless-uid/run')])
    require(os.getuid() == 1000, 'expected host UID 1000')
    for name in ('Dockerfile', 'compose.yaml', '.dockerignore', 'README.md'):
        require((REPO / 'docker/tools/python' / name).is_file(), 'missing ' + name)
    scratch = Path(tempfile.mkdtemp(prefix='scratch.', dir=Path(__file__).parent))
    project = scratch / 'project'
    project.mkdir()
    env = dict(os.environ, DEV_WORKSPACE=str(project))
    compose = DOCKER + ['compose', '-p', TOKEN, '-f',
                        str(REPO / 'docker/tools/python/compose.yaml'), '--profile', '*']
    cfg = json.loads(call(compose + ['config', '--format', 'json'], capture=True, env=env))
    validate(cfg)
    for path in sorted((REPO / 'docker/labs').rglob('compose.yaml')):
        validate(json.loads(call(DOCKER + ['compose', '-f', str(path), 'config', '--format', 'json'],
                                 capture=True)))
    for name, s in cfg['services'].items():
        require(s['user'] == '0:0' and s['read_only'], name + ': identity/rootfs')
        require(int(s['mem_limit']) == 268435456 and float(s['cpus']) == 0.5, name + ': limits')
        require(s['pids_limit'] == 64 and s['network_mode'] == 'none', name + ': pids/network')
        require(s['cap_drop'] == ['ALL'] and not s.get('cap_add'), name + ': capabilities')
        require('no-new-privileges:true' in s['security_opt'], name + ': no-new-privileges')
    require(not cfg['services']['sandbox'].get('volumes'), 'sandbox has persistent mount')
    for name in ('edit', 'test'):
        mounts = cfg['services'][name]['volumes']
        require(len(mounts) == 1 and mounts[0]['source'] == str(project)
                and mounts[0]['target'] == '/workspace', name + ': project mount')
        require(bool(mounts[0].get('read_only')) == (name == 'test'), name + ': access mode')
    call(compose + ['build', 'sandbox'], env=env)
    passed('build dev-python')

    def mode(name, code):
        cname = TOKEN + '-' + name
        # A random name is checked absent before create; retain failed runs for safe cleanup.
        require(cname not in docker('container', 'ls', '-a', '--format', '{{.Names}}', capture=True).splitlines(),
                'unexpected existing container')
        result = call(compose + ['run', '--name', cname, '--no-deps', '-T', name,
                                 'python', '-c', code], env=env, check=False)
        info = inspect('container', cname)
        require(info['Config']['Labels'].get('com.docker.compose.project') == TOKEN,
                'Compose container ownership')
        containers.add(info['Id'])
        host = info['HostConfig']
        binds = [m for m in info['Mounts'] if m['Type'] == 'bind']
        if name == 'sandbox':
            require(not binds and not any(m['Type'] == 'volume' for m in info['Mounts']),
                    'sandbox runtime persistent mount')
        else:
            require(len(binds) == 1 and binds[0]['Source'] == str(project)
                    and binds[0]['Destination'] == '/workspace'
                    and binds[0]['RW'] == (name == 'edit'), 'runtime bind mode')
        require(not host['Privileged'] and host['ReadonlyRootfs'], 'runtime privileges')
        require(host['Memory'] == 268435456 and host['NanoCpus'] == 500000000,
                'runtime resource configuration')
        require(host['CapDrop'] == ['ALL'] and not host['CapAdd'], 'runtime caps')
        require(host['NetworkMode'] == 'none', 'runtime network')
        remove_container(info['Id'])
        require(result == 0 and info['State']['ExitCode'] == 0, name + ': failed')

    (project / 'host.txt').write_text('from host')
    mode('edit', """
import os, sys
from pathlib import Path
assert sys.version_info[:3] == (3, 13, 7)
print(sys.version)
assert os.getuid() == os.getgid() == 0
assert Path('host.txt').read_text() == 'from host'
Path('container.txt').write_text('from container')
Path('remove.txt').write_text('remove me')
Path('subdir').mkdir()
Path('subdir/keep.txt').write_text('persistent')
""")
    for p in project.rglob('*'):
        st = p.stat()
        print(f'{p.relative_to(scratch)} uid={st.st_uid} gid={st.st_gid}', flush=True)
        require((st.st_uid, st.st_gid) == (1000, 1000), 'bind ownership')
    require((project / 'container.txt').read_text() == 'from container', 'container -> host')
    (project / 'container.txt').write_text('edited on host')
    (project / 'remove.txt').unlink()
    mode('edit', "from pathlib import Path; assert Path('container.txt').read_text() == 'edited on host'; assert Path('subdir/keep.txt').read_text() == 'persistent'; assert not Path('remove.txt').exists()")
    passed('bind: both directions, edit, unlink, subdirectories, UID/GID, recreation')
    mode('test', """
import errno
from pathlib import Path
assert Path('host.txt').read_text() == 'from host'
try:
    Path('forbidden.txt').write_text('unexpected')
except OSError as e:
    assert e.errno == errno.EROFS, e
    print('Expected EROFS:', e)
else:
    raise AssertionError('TEST wrote to project')
""")
    passed('TEST rejects project write with EROFS')
    mode('sandbox', """
import errno, os, time
from pathlib import Path
assert not Path('/workspace/host.txt').exists()
assert not Path('/var/run/docker.sock').exists()
assert not Path('/run/user/1000/docker.sock').exists()
Path('/workspace/transient').write_text('sandbox')
Path('/tmp/transient').write_text('tmpfs')
try:
    Path('/forbidden').write_text('bad')
except OSError as e:
    assert e.errno == errno.EROFS
else:
    raise AssertionError('rootfs writable')
status = Path('/proc/self/status').read_text()
assert 'CapEff:\t0000000000000000' in status
assert 'NoNewPrivs:\t1' in status
cg = Path('/sys/fs/cgroup')
assert (cg/'memory.max').read_text().strip() == '268435456'
quota, period = map(int, (cg/'cpu.max').read_text().split())
assert quota / period == 0.5
print('memory.max:', (cg/'memory.max').read_text().strip())
print('cpu.max:', quota, period, 'os.cpu_count:', os.cpu_count())
buffer = bytearray(8 * 1024 * 1024)
print('Allocated controlled 8 MiB; memory.current:', (cg/'memory.current').read_text().strip())
def throttled():
    return int(dict(line.split() for line in (cg/'cpu.stat').read_text().splitlines())['nr_throttled'])
before = throttled()
end = time.monotonic() + 1.5
while time.monotonic() < end:
    pass
print('CPU throttled periods:', throttled() - before)
assert throttled() > before
""")
    mode('sandbox', "from pathlib import Path; assert not Path('/workspace/transient').exists(); assert not Path('/tmp/transient').exists()")
    passed('SANDBOX isolation, ephemeral tmpfs, cgroup memory/CPU, CPU throttling')

    candidate = TOKEN + '-data'
    existing = docker('volume', 'ls', '--format', '{{.Name}}', capture=True).splitlines()
    require(candidate not in existing, 'volume exists before lab')
    docker('volume', 'create', '--label', LABEL, candidate)
    volume = candidate
    print('CREATED volume ' + volume, flush=True)
    mount = 'type=volume,src=' + volume + ',dst=/data'
    run_image("from pathlib import Path; Path('/data/keep').write_text('volume survives'); Path('/layer-only').write_text('ephemeral')", [mount], writable=True)
    require(inspect('volume', volume)['Labels'].get('kev-infra.lab') == TOKEN, 'volume survived')
    run_image("from pathlib import Path; assert Path('/data/keep').read_text() == 'volume survives'; assert not Path('/layer-only').exists()", [mount], writable=True)
    passed('named volume survives container removal; writable layer disappears')


def cleanup():
    for cid in list(containers):
        remove_container(cid)
    if volume is not None:
        require(inspect('volume', volume)['Labels'].get('kev-infra.lab') == TOKEN,
                'refusing removal: volume label mismatch')
        docker('volume', 'rm', volume)
    if scratch is not None:
        require(scratch.parent == Path(__file__).resolve().parent
                and scratch.name.startswith('scratch.'), 'unsafe scratch path')
        shutil.rmtree(scratch)


if __name__ == '__main__':
    try:
        main()
    finally:
        cleanup()
