gofetch
=======

Tool to keep a working directory and repo in sync.

Reads configuration and repo<->workspace mapping from `/etc/gofetch.conf`

Applications may request a pull by writing the paths (one per line) to 
`/var/run/gofetch`. No guarentees are made as to when this request will be
processed.