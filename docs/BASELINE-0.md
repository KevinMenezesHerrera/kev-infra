# Baseline 0

Gerado em: 2026-09-03T22:34:57-03:00

## Sistema

Ubuntu 26.04 Resolute

## Armazenamento

- NVMe físico: aproximadamente 238.5 GiB
- EFI: aproximadamente 1 GiB
- LVM PV: aproximadamente 177 GiB
- VG: vg_nvme
- LV ubuntu: 115 GiB ext4 montado em /
- LV shared: 35 GiB ext4 montado em /shared
- Espaço livre no VG: aproximadamente 27 GiB
- Espaço fora do LVM reservado para testes/distros: aproximadamente 60 GiB

## Host

Instalado nativamente:

- Brave Browser via repositório APT oficial
- Git
- OpenSSH client
- curl
- wget
- UFW
- squashfs-tools

Não instalado:

- Snap
- Flatpak
- Docker
- Podman
- QEMU
- libvirt

## Decisões

- Snap removido do host base.
- Flatpak não será instalado por padrão.
- Brave permanece nativo no host.
- Toolchains de projetos devem preferencialmente ficar em containers.
- /shared será tratado separadamente da infraestrutura interna do Ubuntu.
