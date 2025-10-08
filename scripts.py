def l2vpn-ptp()

[DEVICE A]
vlan [vlan-id]
description [nome_do_cliente]

interface vlan [vlan-id]
description [nome_do_cliente]
mpls l2vc [site_a] [l2vc-id] mtu 2000


interface