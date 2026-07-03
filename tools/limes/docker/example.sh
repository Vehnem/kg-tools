wget https://raw.githubusercontent.com/dice-group/LIMES/master/limes-core/resources/lgd-lgd-optional-properties.xml
# Run mapping against endpoint and get job id
curl -F config_file=@lgd-lgd-optional-properties.xml  http://localhost:port/submit
# returns:
# {"requestId":"7538819321022935531","success":true}
# Observe the status
curl http://localhost:port/status/requestId
# returns:
# {"status":{"code":2,"description":"Request has been processed"},"success":true}
# Get result file list
curl http://localhost:port/results/requestId
# returns:
# {"availableOperators":["lgd_relaybox_near.nt","lgd_relaybox_verynear.nt"],"success":true}
# Get result
curl http://localhost:port/result/requestId/lgd_relaybox_verynear.nt
# returns:
# <http://linkedgeodata.org/triplify/node2806760713>    <http://linkedgeodata.org/triplify/node2806760713>    1.0
# <http://linkedgeodata.org/triplify/node2806760713>    <http://linkedgeodata.org/triplify/node400957326>    0.9283311463354712
# <http://linkedgeodata.org/triplify/node1319713883>    <http://linkedgeodata.org/triplify/node1319713883>    1.0
# [...]
# Inspect the logs
curl http://localhost:port/logs/requestId
# returns:
# 2018-06-20T12:08:09,027 [ForkJoinPool.commonPool-worker-2] INFO org.aksw.limes.core.io.cache.HybridCache 111 - Checking for file [...]
