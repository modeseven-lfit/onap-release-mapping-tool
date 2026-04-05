# ONAP Release Manifest: Master

- **Generated:** 2026-04-05T16:13:54Z
- **Tool version:** 0.4.0
- **Schema version:** 1.1.0
- **OOM chart version:** 18.0.0

## Summary

- **Total repositories:** 218
- **Total Docker images:** 85
- **Total Helm components:** 98

## Repositories

| Gerrit Project | Category | Confidence | State | Maintained | Has CI |
| -------------- | -------- | ---------- | ----- | ---------- | ------ |
| aai | runtime | medium | ☑️ | Yes |  |
| aai/aai-common | runtime | high | ✅ | Yes | Yes |
| aai/babel | runtime | high | ✅ | Yes | Yes |
| aai/graphadmin | runtime | high | ✅ | Yes | Yes |
| aai/graphgraph | runtime | medium | ❓ | Yes | Yes |
| aai/logging-service | runtime | medium | ❓ | Yes | Yes |
| aai/model-loader | runtime | high | ✅ | Yes | Yes |
| aai/oom | runtime | medium | ❓ | Yes |  |
| aai/resources | runtime | high | ✅ | Yes | Yes |
| aai/rest-client | runtime | medium | ❓ | Yes | Yes |
| aai/schema-service | runtime | high | ✅ | Yes | Yes |
| aai/sparky-be | runtime | high | ✅ | Yes | Yes |
| aai/sparky-fe | runtime | medium | ❓ | Yes | Yes |
| aai/test-config | runtime | medium | ❓ | Yes |  |
| aai/traversal | runtime | high | ✅ | Yes | Yes |
| ccsdk | runtime | medium | ☑️ | Yes |  |
| ccsdk/apps | runtime | high | ✅ | Yes | Yes |
| ccsdk/cds | runtime | high | ✅ | Yes | Yes |
| ccsdk/distribution | runtime | high | ✅ | Yes | Yes |
| ccsdk/features | runtime | medium | ❓ | Yes | Yes |
| ccsdk/oran | runtime | high | ✅ | Yes | Yes |
| ccsdk/parent | runtime | medium | ❓ | Yes | Yes |
| ccsdk/platform/blueprints | runtime | medium | ❓ | Yes |  |
| ccsdk/sli | runtime | medium | ❓ | Yes | Yes |
| ccsdk/storage/esaas | runtime | medium | ❓ | Yes |  |
| ci-management | runtime | medium | ❓ | Yes | Yes |
| cli | runtime | medium | ❓ | Yes |  |
| cps | runtime | high | ☑️ | Yes | Yes |
| cps/cps-tbdmt | runtime | medium | ❓ | Yes |  |
| cps/cps-temporal | runtime | medium | ❓ | Yes |  |
| cps/ncmp-dmi-plugin | runtime | high | ✅ | Yes | Yes |
| dcaegen2 | runtime | medium | ☑️ | Yes |  |
| dcaegen2/analytics/tca-gen2 | runtime | medium | ❓ | Yes |  |
| dcaegen2/collectors/datafile | runtime | medium | ❓ | Yes |  |
| dcaegen2/collectors/hv-ves | runtime | high | ✅ | Yes |  |
| dcaegen2/collectors/restconf | runtime | medium | ❓ | Yes |  |
| dcaegen2/collectors/snmptrap | runtime | medium | ❓ | Yes |  |
| dcaegen2/collectors/ves | runtime | high | ✅ | Yes |  |
| dcaegen2/deployments | runtime | high | ✅ | Yes |  |
| dcaegen2/platform | runtime | medium | ☑️ | Yes | Yes |
| dcaegen2/platform/blueprints | runtime | medium | ❓ | Yes |  |
| dcaegen2/platform/ves-openapi-manager | runtime | high | ✅ | Yes |  |
| dcaegen2/services | runtime | high | ☑️ | Yes | Yes |
| dcaegen2/services/heartbeat | runtime | medium | ❓ | Yes |  |
| dcaegen2/services/mapper | runtime | medium | ❓ | Yes |  |
| dcaegen2/services/pm-mapper | runtime | medium | ❓ | Yes | Yes |
| dcaegen2/services/prh | runtime | high | ✅ | Yes |  |
| dcaegen2/services/sdk | runtime | medium | ❓ | Yes |  |
| dcaegen2/services/son-handler | runtime | medium | ❓ | Yes |  |
| dcaegen2/utils | runtime | medium | ❓ | Yes |  |
| demo | runtime | medium | ❓ | Yes | Yes |
| dmaap | runtime | medium | ❓ | Yes |  |
| dmaap/buscontroller | runtime | medium | ❓ | Yes |  |
| dmaap/datarouter | runtime | medium | ❓ | Yes |  |
| dmaap/kafka11aaf | runtime | medium | ❓ | Yes |  |
| dmaap/messagerouter/dmaapclient | runtime | medium | ❓ | Yes |  |
| dmaap/messagerouter/messageservice | runtime | medium | ❓ | Yes |  |
| dmaap/zookeeper | runtime | medium | ❓ | Yes |  |
| doc | runtime | medium | ❓ | Yes |  |
| doc/doc-best-practice | runtime | medium | ❓ |  |  |
| holmes | runtime | medium | ❓ | Yes |  |
| holmes/common | runtime | medium | ❓ | Yes |  |
| holmes/engine-management | runtime | medium | ❓ | Yes |  |
| holmes/rule-management | runtime | medium | ❓ | Yes |  |
| integration | runtime | medium | ❓ | Yes | Yes |
| integration/csit | runtime | medium | ❓ | Yes |  |
| integration/data-provider | runtime | medium | ❓ | Yes | Yes |
| integration/docker/onap-java11 | runtime | medium | ❓ | Yes | Yes |
| integration/docker/onap-python | runtime | medium | ❓ | Yes | Yes |
| integration/gating | runtime | medium | ❓ |  | Yes |
| integration/ietf-actn-tools | runtime | medium | ❓ | Yes | Yes |
| integration/onap-component-simulators | runtime | medium | ❓ |  | Yes |
| integration/pipelines/build-integration | runtime | medium | ❓ |  |  |
| integration/pipelines/chained-ci | runtime | medium | ❓ |  |  |
| integration/pipelines/oom-automatic-installation | runtime | medium | ❓ |  |  |
| integration/pipelines/xtesting-onap | runtime | medium | ❓ |  |  |
| integration/python-onapsdk | runtime | medium | ❓ |  | Yes |
| integration/seccom | runtime | medium | ❓ | Yes | Yes |
| integration/simulators/5G-core-nf-simulator | runtime | medium | ❓ | Yes | Yes |
| integration/simulators/A1-policy-enforcement-simulator | runtime | medium | ❓ | Yes | Yes |
| integration/simulators/core-nssmf-simulator | runtime | medium | ❓ | Yes | Yes |
| integration/simulators/nf-simulator | runtime | medium | ❓ | Yes | Yes |
| integration/simulators/nf-simulator/avcn-manager | runtime | medium | ❓ | Yes | Yes |
| integration/simulators/nf-simulator/netconf-server | runtime | medium | ❓ | Yes | Yes |
| integration/simulators/nf-simulator/pm-https-server | runtime | medium | ❓ | Yes | Yes |
| integration/simulators/nf-simulator/ves-client | runtime | medium | ❓ | Yes | Yes |
| integration/simulators/pnf-simulator | runtime | medium | ❓ | Yes | Yes |
| integration/simulators/ran-app | runtime | medium | ❓ |  |  |
| integration/simulators/ran-nssmf-simulator | runtime | medium | ❓ | Yes | Yes |
| integration/simulators/ran-simulator | runtime | medium | ❓ | Yes | Yes |
| integration/usecases/A1-policy-enforcement | runtime | medium | ❓ | Yes | Yes |
| integration/usecases/A1-policy-enforcement-r-apps | runtime | medium | ❓ | Yes | Yes |
| integration/xtesting | runtime | medium | ❓ | Yes | Yes |
| modeling/etsicatalog | runtime | medium | ❓ | Yes |  |
| modeling/modelspec | runtime | medium | ❓ | Yes |  |
| modeling/toscaparsers | runtime | medium | ❓ | Yes |  |
| msb | runtime | medium | ❓ | Yes |  |
| msb/apigateway | runtime | medium | ❓ | Yes | Yes |
| msb/discovery | runtime | medium | ❓ | Yes | Yes |
| msb/java-sdk | runtime | medium | ❓ | Yes | Yes |
| msb/service-mesh | runtime | medium | ❓ | Yes |  |
| msb/swagger-sdk | runtime | medium | ❓ | Yes | Yes |
| multicloud | runtime | medium | ☑️ | Yes | Yes |
| multicloud/framework | runtime | high | ✅ | Yes | Yes |
| multicloud/k8s | runtime | high | ✅ | Yes |  |
| multicloud/openstack | runtime | high | ☑️ | Yes | Yes |
| multicloud/openstack/vmware | runtime | medium | ❓ | Yes | Yes |
| multicloud/openstack/windriver | runtime | medium | ❓ | Yes |  |
| oom | infrastructure | high | ☑️ | Yes | Yes |
| oom/consul | runtime | medium | ❓ | Yes | Yes |
| oom/offline-installer | runtime | medium | ❓ | Yes |  |
| oom/platform/cert-manager | runtime | medium | ❓ | Yes |  |
| oom/platform/cert-service | runtime | high | ✅ | Yes | Yes |
| oom/platform/keycloak | runtime | medium | ❓ | Yes |  |
| oom/readiness | runtime | medium | ❓ | Yes | Yes |
| oom/registrator | runtime | medium | ❓ | Yes | Yes |
| oom/utils | runtime | medium | ❓ | Yes |  |
| oparent | runtime | medium | ❓ | Yes | Yes |
| oparent/cia | runtime | medium | ❓ | Yes |  |
| optf | runtime | medium | ❓ | Yes |  |
| optf/has | runtime | medium | ❓ | Yes |  |
| optf/osdf | runtime | medium | ❓ | Yes |  |
| osa | runtime | medium | ❓ | Yes |  |
| policy | runtime | medium | ☑️ | Yes |  |
| policy/apex-pdp | runtime | high | ✅ | Yes | Yes |
| policy/api | runtime | high | ✅ | Yes | Yes |
| policy/clamp | runtime | high | ✅ | Yes | Yes |
| policy/common | runtime | medium | ❓ | Yes | Yes |
| policy/distribution | runtime | high | ✅ | Yes | Yes |
| policy/docker | runtime | high | ✅ | Yes | Yes |
| policy/drools-applications | runtime | medium | ❓ | Yes | Yes |
| policy/drools-pdp | runtime | high | ✅ | Yes | Yes |
| policy/gui | runtime | medium | ❓ | Yes |  |
| policy/models | runtime | medium | ❓ | Yes | Yes |
| policy/opa-pdp | runtime | high | ✅ |  |  |
| policy/pap | runtime | high | ✅ | Yes | Yes |
| policy/parent | runtime | medium | ❓ | Yes | Yes |
| policy/xacml-pdp | runtime | high | ✅ | Yes | Yes |
| portal-ng | runtime | medium | ❓ |  |  |
| portal-ng/bff | runtime | high | ✅ |  | Yes |
| portal-ng/e2e | runtime | medium | ❓ |  |  |
| portal-ng/history | runtime | high | ✅ |  | Yes |
| portal-ng/preferences | runtime | high | ✅ |  | Yes |
| portal-ng/ui | runtime | high | ✅ |  | Yes |
| relman | runtime | medium | ❓ | Yes |  |
| sandbox-2 | runtime | medium | ❓ | Yes |  |
| sandbox-3 | runtime | medium | ❓ | Yes |  |
| sdc | runtime | high | ☑️ | Yes | Yes |
| sdc/onap-ui-angular | runtime | medium | ❓ | Yes | Yes |
| sdc/onap-ui-common | runtime | medium | ❓ | Yes | Yes |
| sdc/sdc-be-common | runtime | medium | ❓ | Yes | Yes |
| sdc/sdc-distribution-client | runtime | medium | ❓ | Yes | Yes |
| sdc/sdc-docker-base | runtime | medium | ❓ | Yes |  |
| sdc/sdc-helm-validator | runtime | high | ✅ | Yes | Yes |
| sdc/sdc-pubsub | runtime | medium | ❓ | Yes | Yes |
| sdc/sdc-tosca | runtime | medium | ❓ | Yes | Yes |
| sdc/sdc-workflow-designer | runtime | high | ✅ | Yes | Yes |
| sdnc | runtime | medium | ☑️ | Yes |  |
| sdnc/apps | runtime | medium | ❓ | Yes | Yes |
| sdnc/northbound | runtime | medium | ❓ | Yes | Yes |
| sdnc/oam | runtime | high | ✅ | Yes | Yes |
| so | runtime | high | ☑️ | Yes | Yes |
| so/adapters/so-cnf-adapter | runtime | medium | ❓ | Yes | Yes |
| so/adapters/so-etsi-sol003-adapter | runtime | high | ✅ | Yes | Yes |
| so/adapters/so-etsi-sol005-adapter | runtime | high | ✅ | Yes | Yes |
| so/adapters/so-nssmf-adapter | runtime | high | ✅ | Yes | Yes |
| so/adapters/so-oof-adapter | runtime | high | ✅ | Yes | Yes |
| so/chef-repo | runtime | medium | ❓ | Yes |  |
| so/docker-config | runtime | medium | ❓ | Yes |  |
| so/libs | runtime | medium | ❓ | Yes | Yes |
| so/so-admin-cockpit | runtime | high | ✅ | Yes | Yes |
| so/so-config | runtime | medium | ❓ | Yes |  |
| so/so-etsi-nfvo | runtime | medium | ❓ | Yes | Yes |
| spark-model-runner | runtime | medium | ❓ | Yes |  |
| testsuite | runtime | high | ☑️ | Yes |  |
| testsuite/cds | runtime | medium | ❓ | Yes | Yes |
| testsuite/cds-mock-odl | runtime | medium | ❓ | Yes | Yes |
| testsuite/cds-mock-server | runtime | medium | ❓ | Yes | Yes |
| testsuite/cds-mock-ssh | runtime | medium | ❓ | Yes | Yes |
| testsuite/cds-modk-odl | runtime | medium | ❓ |  | Yes |
| testsuite/oom | runtime | medium | ❓ | Yes |  |
| testsuite/python-testing-utils | runtime | medium | ❓ | Yes | Yes |
| testsuite/pythonsdk-tests | runtime | medium | ❓ | Yes | Yes |
| testsuite/robot-utils | runtime | medium | ❓ | Yes |  |
| university | runtime | medium | ❓ | Yes |  |
| usecase-ui | runtime | high | ☑️ | Yes | Yes |
| usecase-ui/intent-analysis | runtime | high | ✅ |  | Yes |
| usecase-ui/llm-adaptation | runtime | high | ✅ |  | Yes |
| usecase-ui/nlp | runtime | high | ✅ | Yes | Yes |
| usecase-ui/server | runtime | high | ✅ | Yes | Yes |
| vfc | runtime | medium | ❓ | Yes |  |
| vfc/gvnfm/vnflcm | runtime | medium | ❓ | Yes |  |
| vfc/gvnfm/vnfmgr | runtime | medium | ❓ | Yes |  |
| vfc/gvnfm/vnfres | runtime | medium | ❓ | Yes |  |
| vfc/nfvo/db | runtime | medium | ❓ | Yes |  |
| vfc/nfvo/driver/vnfm/gvnfm | runtime | medium | ❓ | Yes |  |
| vfc/nfvo/driver/vnfm/svnfm | runtime | medium | ❓ | Yes |  |
| vfc/nfvo/lcm | runtime | medium | ❓ | Yes |  |
| vnfrqts | runtime | medium | ❓ | Yes |  |
| vnfrqts/epics | runtime | medium | ❓ | Yes |  |
| vnfrqts/guidelines | runtime | medium | ❓ | Yes |  |
| vnfrqts/requirements | runtime | medium | ❓ | Yes |  |
| vnfrqts/testcases | runtime | medium | ❓ | Yes |  |
| vnfrqts/usecases | runtime | medium | ❓ | Yes |  |
| vnfsdk | runtime | medium | ❓ | Yes |  |
| vnfsdk/dovetail-integration | runtime | medium | ❓ | Yes |  |
| vnfsdk/functest | runtime | medium | ❓ | Yes |  |
| vnfsdk/lctest | runtime | medium | ❓ | Yes | Yes |
| vnfsdk/model | runtime | medium | ❓ | Yes |  |
| vnfsdk/pkgtools | runtime | medium | ❓ | Yes | Yes |
| vnfsdk/refrepo | runtime | medium | ❓ | Yes |  |
| vnfsdk/validation | runtime | medium | ❓ | Yes |  |
| vvp | runtime | medium | ❓ | Yes |  |
| vvp/documentation | runtime | medium | ❓ | Yes |  |
| vvp/engagementmgr | runtime | medium | ❓ | Yes |  |
| vvp/regression-tests | runtime | medium | ❓ | Yes |  |
| vvp/test-engine | runtime | medium | ❓ | Yes |  |
| vvp/validation-scripts | runtime | medium | ❓ | Yes |  |

### Totals

| Total | State | Description |
| ----: | :---: | ----------- |
| 46 | ✅ | In current ONAP release |
| 15 | ☑️ | Parent project (children in release) |
| 157 | ❓ | Undetermined |

## Docker Images

| Image | Tag | Gerrit Project | Registry | Validated |
| ----- | --- | -------------- | -------- | --------- |
| onap/aai-graphadmin | 1.16.0 | aai/graphadmin | nexus3.onap.org:10001 | Yes |
| onap/aai-haproxy | 1.15.2 | aai/aai-common | nexus3.onap.org:10001 | Yes |
| onap/aai-resources | 1.16.0 | aai/resources | nexus3.onap.org:10001 | Yes |
| onap/aai-schema-service | 1.12.11 | aai/schema-service | nexus3.onap.org:10001 | Yes |
| onap/aai-traversal | 1.16.0 | aai/traversal | nexus3.onap.org:10001 | Yes |
| onap/babel | 1.13.5 | aai/babel | nexus3.onap.org:10001 | Yes |
| onap/ccsdk-apps-ms-neng | 1.4.0 | ccsdk/apps | nexus3.onap.org:10001 | Yes |
| onap/ccsdk-blueprintsprocessor | 1.8.1 | ccsdk/cds | nexus3.onap.org:10001 | Yes |
| onap/ccsdk-cds-ui-server | 1.8.1 | ccsdk/cds | nexus3.onap.org:10001 | Yes |
| onap/ccsdk-commandexecutor | 1.8.1 | ccsdk/cds | nexus3.onap.org:10001 | Yes |
| onap/ccsdk-dgbuilder-image | 2.2.0 | ccsdk/distribution | nexus3.onap.org:10001 | Yes |
| onap/ccsdk-oran-a1policymanagementservice | 2.2.0 | ccsdk/oran | nexus3.onap.org:10001 | Yes |
| onap/ccsdk-py-executor | 1.8.1 | ccsdk/cds | nexus3.onap.org:10001 | Yes |
| onap/ccsdk-sdclistener | 1.8.1 | ccsdk/cds | nexus3.onap.org:10001 | Yes |
| onap/cps-and-ncmp | 3.7.0 | cps | nexus3.onap.org:10001 | Yes |
| onap/cps-temporal | 1.2.1 | cps | nexus3.onap.org:10001 | Yes |
| onap/model-loader | 1.14.3 | aai/model-loader | nexus3.onap.org:10001 | Yes |
| onap/multicloud/framework | 1.9.2 | multicloud/framework | nexus3.onap.org:10001 | Yes |
| onap/multicloud/framework-artifactbroker | 1.9.3 | multicloud/framework | nexus3.onap.org:10001 | Yes |
| onap/multicloud/k8s | 0.12.0 | multicloud/k8s | nexus3.onap.org:10001 | Yes |
| onap/multicloud/openstack-fcaps | 1.5.7 | multicloud/openstack | nexus3.onap.org:10001 | Yes |
| onap/music/prom | 1.0.5 | music/prom | nexus3.onap.org:10001 | Yes |
| onap/ncmp-dmi-plugin | 1.7.0 | cps/ncmp-dmi-plugin | nexus3.onap.org:10001 | Yes |
| onap/org.onap.dcaegen2.collectors.hv-ves.hv-collector-main | 1.11.0 | dcaegen2/collectors/hv-ves | nexus3.onap.org:10001 | Yes |
| onap/org.onap.dcaegen2.collectors.ves.vescollector | 1.12.4 | dcaegen2/collectors/ves | nexus3.onap.org:10001 | Yes |
| onap/org.onap.dcaegen2.deployments.healthcheck-container | 2.4.1 | dcaegen2/deployments | nexus3.onap.org:10001 | Yes |
| onap/org.onap.dcaegen2.platform.ves-openapi-manager | 1.3.1 | dcaegen2/platform/ves-openapi-manager | nexus3.onap.org:10001 | Yes |
| onap/org.onap.dcaegen2.services.datalake.exposure.service | 1.1.3 | dcaegen2/services | nexus3.onap.org:10001 | Yes |
| onap/org.onap.dcaegen2.services.datalakeadminui | 1.1.3 | dcaegen2/services | nexus3.onap.org:10001 | Yes |
| onap/org.onap.dcaegen2.services.datalakefeeder | 1.1.3 | dcaegen2/services | nexus3.onap.org:10001 | Yes |
| onap/org.onap.dcaegen2.services.prh.prh-app-server | 1.12.0 | dcaegen2/services/prh | nexus3.onap.org:10001 | Yes |
| onap/org.onap.oom.platform.cert-service.oom-certservice-api | 2.6.0 | oom/platform/cert-service | nexus3.onap.org:10001 | Yes |
| onap/org.onap.oom.platform.cert-service.oom-certservice-k8s-external-provider | 2.6.0 | oom/platform/cert-service | nexus3.onap.org:10001 | Yes |
| onap/policy-apex-pdp | 4.2.2 | policy/apex-pdp | nexus3.onap.org:10001 | Yes |
| onap/policy-api | 4.2.2 | policy/api | nexus3.onap.org:10001 | Yes |
| onap/policy-clamp-ac-a1pms-ppnt | 9.0.0 | policy/clamp | nexus3.onap.org:10001 | Yes |
| onap/policy-clamp-ac-http-ppnt | 9.0.0 | policy/clamp | nexus3.onap.org:10001 | Yes |
| onap/policy-clamp-ac-k8s-ppnt | 8.2.2 | policy/clamp | nexus3.onap.org:10001 | Yes |
| onap/policy-clamp-ac-kserve-ppnt | 9.0.0 | policy/clamp | nexus3.onap.org:10001 | Yes |
| onap/policy-clamp-ac-pf-ppnt | 9.0.0 | policy/clamp | nexus3.onap.org:10001 | Yes |
| onap/policy-clamp-runtime-acm | 8.2.2 | policy/clamp | nexus3.onap.org:10001 | Yes |
| onap/policy-db-migrator | 4.2.2 | policy/docker | nexus3.onap.org:10001 | Yes |
| onap/policy-distribution | 4.2.2 | policy/distribution | nexus3.onap.org:10001 | Yes |
| onap/policy-opa-pdp | 1.0.8 | policy/opa-pdp | nexus3.onap.org:10001 | Yes |
| onap/policy-pap | 4.2.2 | policy/pap | nexus3.onap.org:10001 | Yes |
| onap/policy-pdpd-cl | 3.2.2 | policy/drools-pdp | nexus3.onap.org:10001 | Yes |
| onap/policy-xacml-pdp | 4.2.2 | policy/xacml-pdp | nexus3.onap.org:10001 | Yes |
| onap/portal-ng/bff | latest | portal-ng/bff | nexus3.onap.org:10001 | Yes |
| onap/portal-ng/history | latest | portal-ng/history | nexus3.onap.org:10001 | Yes |
| onap/portal-ng/preferences | latest | portal-ng/preferences | nexus3.onap.org:10001 | Yes |
| onap/portal-ng/ui | latest | portal-ng/ui | nexus3.onap.org:10001 | Yes |
| onap/sdc-backend-all-plugins | 1.15.0 | sdc | nexus3.onap.org:10001 | Yes |
| onap/sdc-cassandra | 1.15.0 | sdc | nexus3.onap.org:10001 | Yes |
| onap/sdc-frontend | 1.15.0 | sdc | nexus3.onap.org:10001 | Yes |
| onap/sdc-helm-validator | 1.3.3 | sdc/sdc-helm-validator | nexus3.onap.org:10001 | Yes |
| onap/sdc-onboard-backend | 1.15.0 | sdc | nexus3.onap.org:10001 | Yes |
| onap/sdc-workflow-backend | 1.14.1 | sdc/sdc-workflow-designer | nexus3.onap.org:10001 | Yes |
| onap/sdc-workflow-frontend | 1.14.1 | sdc/sdc-workflow-designer | nexus3.onap.org:10001 | Yes |
| onap/sdnc-ansible-server-image | 3.2.4 | sdnc/oam | nexus3.onap.org:10001 | Yes |
| onap/sdnc-image | 3.2.4 | sdnc/oam | nexus3.onap.org:10001 | Yes |
| onap/sdnc-ueb-listener-image | 3.2.4 | sdnc/oam | nexus3.onap.org:10001 | Yes |
| onap/sdnc-web-image | 3.2.4 | sdnc/oam | nexus3.onap.org:10001 | Yes |
| onap/so/api-handler-infra | 1.17.0 | so | nexus3.onap.org:10001 | Yes |
| onap/so/bpmn-infra | 1.17.0 | so | nexus3.onap.org:10001 | Yes |
| onap/so/catalog-db-adapter | 1.17.0 | so | nexus3.onap.org:10001 | Yes |
| onap/so/openstack-adapter | 1.17.0 | so | nexus3.onap.org:10001 | Yes |
| onap/so/request-db-adapter | 1.17.0 | so | nexus3.onap.org:10001 | Yes |
| onap/so/sdc-controller | 1.17.0 | so | nexus3.onap.org:10001 | Yes |
| onap/so/sdnc-adapter | 1.17.0 | so | nexus3.onap.org:10001 | Yes |
| onap/so/so-admin-cockpit | 1.10.0 | so/so-admin-cockpit | nexus3.onap.org:10001 | Yes |
| onap/so/so-cnf-adapter | 1.13.1 | so | nexus3.onap.org:10001 | Yes |
| onap/so/so-cnfm-as-lcm | 1.13.1 | so | nexus3.onap.org:10001 | Yes |
| onap/so/so-etsi-nfvo-ns-lcm | 1.9.0 | so | nexus3.onap.org:10001 | Yes |
| onap/so/so-etsi-sol003-adapter | 1.10.0 | so/adapters/so-etsi-sol003-adapter | nexus3.onap.org:10001 | Yes |
| onap/so/so-etsi-sol005-adapter | 1.10.0 | so/adapters/so-etsi-sol005-adapter | nexus3.onap.org:10001 | Yes |
| onap/so/so-nssmf-adapter | 1.11.1 | so/adapters/so-nssmf-adapter | nexus3.onap.org:10001 | Yes |
| onap/so/so-oof-adapter | 1.10.2 | so/adapters/so-oof-adapter | nexus3.onap.org:10001 | Yes |
| onap/so/ve-vnfm-adapter | 1.6.4 | so | nexus3.onap.org:10001 | Yes |
| onap/sparky-be | 2.1.0 | aai/sparky-be | nexus3.onap.org:10001 | Yes |
| onap/testsuite | 1.14.0 | testsuite | nexus3.onap.org:10001 | Yes |
| onap/usecase-ui | 16.0.1 | usecase-ui | nexus3.onap.org:10001 | Yes |
| onap/usecase-ui-intent-analysis | 16.0.1 | usecase-ui/intent-analysis | nexus3.onap.org:10001 | Yes |
| onap/usecase-ui-llm-adaptation | 16.0.1 | usecase-ui/llm-adaptation | nexus3.onap.org:10001 | Yes |
| onap/usecase-ui-nlp | 1.0.5 | usecase-ui/nlp | nexus3.onap.org:10001 | Yes |
| onap/usecase-ui-server | 16.0.1 | usecase-ui/server | nexus3.onap.org:10001 | Yes |

## Helm Components

| Name | Version | Enabled | Condition Key |
| ---- | ------- | ------- | ------------- |
| a1policymanagement | ~13.x-0 | No | a1policymanagement.enabled |
| aai | ~16.x-0 | No | aai.enabled |
| aai-babel | 15.0.2 |  |  |
| aai-graphadmin | 16.0.0 |  |  |
| aai-modelloader | 15.0.5 |  |  |
| aai-resources | 16.0.0 |  |  |
| aai-schema-service | 16.0.0 |  |  |
| aai-sparky-be | 16.0.0 |  |  |
| aai-traversal | 16.0.0 |  |  |
| authentication | ~15.x-0 | No | authentication.enabled |
| cds | ~16.x-0 | No | cds.enabled |
| cds-blueprints-processor | 13.0.1 |  |  |
| cds-command-executor | 13.0.0 |  |  |
| cds-py-executor | 13.0.0 |  |  |
| cds-sdc-listener | 13.0.0 |  |  |
| cds-ui | 13.0.0 |  |  |
| chartmuseum | 13.0.0 |  |  |
| cmpv2-cert-provider | 13.0.0 |  |  |
| cps | ~13.x-0 | No | cps.enabled |
| cps-core | 13.0.2 |  |  |
| cps-temporal | 13.0.1 |  |  |
| dcae-datalake-admin-ui | 13.0.1 |  |  |
| dcae-datalake-des | 13.0.1 |  |  |
| dcae-datalake-feeder | 13.0.1 |  |  |
| dcae-hv-ves-collector | 13.0.0 |  |  |
| dcae-ms-healthcheck | 13.0.0 |  |  |
| dcae-prh | 14.0.0 |  |  |
| dcae-ves-collector | 13.1.1 |  |  |
| dcae-ves-openapi-manager | 13.0.0 |  |  |
| dcaegen2-services | ~16.x-0 | No | dcaegen2-services.enabled |
| dgbuilder | 15.1.0 |  |  |
| multicloud | ~15.x-0 | No | multicloud.enabled |
| multicloud-fcaps | 13.0.0 |  |  |
| multicloud-k8s | 13.3.0 |  |  |
| ncmp-dmi-plugin | 13.0.1 |  |  |
| network-name-gen | 16.0.0 |  |  |
| onap-keycloak-config-cli | 6.2.1 |  |  |
| oom-cert-service | 13.0.0 |  |  |
| platform | ~13.x-0 | No | platform.enabled |
| policy | ~17.x-0 | No | policy.enabled |
| policy-apex-pdp | 17.0.0 |  |  |
| policy-api | 17.0.0 |  |  |
| policy-clamp-ac-a1pms-ppnt | 17.0.1 |  |  |
| policy-clamp-ac-http-ppnt | 17.0.1 |  |  |
| policy-clamp-ac-k8s-ppnt | 17.0.0 |  |  |
| policy-clamp-ac-kserve-ppnt | 17.0.1 |  |  |
| policy-clamp-ac-pf-ppnt | 17.0.1 |  |  |
| policy-clamp-runtime-acm | 17.0.0 |  |  |
| policy-distribution | 17.0.0 |  |  |
| policy-drools-pdp | 17.0.0 |  |  |
| policy-nexus | 17.0.0 |  |  |
| policy-opa-pdp | 17.0.0 |  |  |
| policy-pap | 17.0.0 |  |  |
| policy-xacml-pdp | 17.0.0 |  |  |
| portal-ng | ~14.x-0 | No | portal-ng.enabled |
| portal-ng-bff | 13.1.1 |  |  |
| portal-ng-history | 14.1.1 |  |  |
| portal-ng-preferences | 14.1.1 |  |  |
| portal-ng-ui | 13.0.1 |  |  |
| robot | ~13.x-0 | No | robot.enabled |
| sdc | ~13.x-0 | No | sdc.enabled |
| sdc-be | 13.0.5 |  |  |
| sdc-cs | 13.0.5 |  |  |
| sdc-fe | 13.0.4 |  |  |
| sdc-helm-validator | 13.0.1 |  |  |
| sdc-onboarding-be | 13.0.5 |  |  |
| sdc-wfd-be | 13.0.5 |  |  |
| sdc-wfd-fe | 13.0.4 |  |  |
| sdnc | ~16.x-0 | No | sdnc.enabled |
| sdnc-ansible-server | 15.1.0 |  |  |
| sdnc-prom | 13.0.0 |  |  |
| sdnc-web | 15.1.0 |  |  |
| so | ~17.x-0 | No | so.enabled |
| so-admin-cockpit | 15.0.0 |  |  |
| so-bpmn-infra | 17.0.0 |  |  |
| so-catalog-db-adapter | 17.0.0 |  |  |
| so-cnf-adapter | 15.0.1 |  |  |
| so-cnfm-lcm | 13.0.0 |  |  |
| so-etsi-nfvo-ns-lcm | 13.0.0 |  |  |
| so-etsi-sol003-adapter | 13.0.0 |  |  |
| so-etsi-sol005-adapter | 13.0.0 |  |  |
| so-mariadb | 16.0.0 |  |  |
| so-nssmf-adapter | 15.0.0 |  |  |
| so-oof-adapter | 15.0.0 |  |  |
| so-openstack-adapter | 17.0.0 |  |  |
| so-request-db-adapter | 17.0.0 |  |  |
| so-sdc-controller | 17.0.0 |  |  |
| so-sdnc-adapter | 17.0.0 |  |  |
| so-ve-vnfm-adapter | 13.0.0 |  |  |
| soHelpers | 13.0.1 |  |  |
| strimzi | ~16.x-0 | No | strimzi.enabled |
| strimzi-kafka-bridge | 13.0.3 |  |  |
| ueb-listener | 15.1.0 |  |  |
| uui | ~16.x-0 | No | uui.enabled |
| uui-intent-analysis | 16.0.1 |  |  |
| uui-llm-adaptation | 16.0.1 |  |  |
| uui-nlp | 13.0.0 |  |  |
| uui-server | 16.0.1 |  |  |
