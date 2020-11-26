from xml.dom.minidom import parse
import xml.dom.minidom

DOMTree = xml.dom.minidom.parse("config.xml")
root = DOMTree.documentElement
hosts = root.getElementsByTagName("host")

# Print detail of each movie.
for host in hosts:
	if host.getAttribute('name') == 'simulator':
		ber_rate = host.getElementsByTagName('ber_rate')[0]
		print('ber_rate', ber_rate.childNodes[0].data)
	ip = host.getElementsByTagName('ip')[0]
	print('ip', ip.childNodes[0].data)