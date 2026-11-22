FROM curlimages/curl:8.11.1
COPY garage/init.sh /init.sh
ENTRYPOINT ["/bin/sh", "/init.sh"]
