#!/bin/bash

# HTTPS (TLS) proxy address
PACHTTPSHOST='proxy-ssl.antizapret.prostovpn.org:3143'

# Usual proxy address
PACPROXYHOST='proxy-nossl.antizapret.prostovpn.org:29976' 

# Special proxy address for ranges
PACPROXYSPECIAL='CCAHIHA.antizapret.prostovpn.org:3128'

PACFILE="result/proxy-host-ssl.pac"
PACFILE_NOSSL="result/proxy-host-nossl.pac"