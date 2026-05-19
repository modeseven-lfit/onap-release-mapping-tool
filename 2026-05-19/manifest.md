# ONAP Release Manifest: Master

- **Generated:** 2026-05-19T14:41:51Z
- **Tool version:** 0.0.1.dev1
- **Schema version:** 1.2.0
- **OOM chart version:** 18.0.0

## Summary

- **Total repositories:** 217
- **Total Docker images:** 89
- **Total Helm components:** 98

## Repositories

<div class="summary">
  <p><strong>At a glance</strong></p>
  <p><strong>Total repositories:</strong> 217</p>
  <p><strong>In current ONAP release:</strong> 73 of 217</p>
  <p><strong>Read-only / archived:</strong> 0 of 217</p>
  <p><strong>Maintained:</strong> 198 Yes, 0 No, 19 — (not listed in relman)</p>
  <p><strong>Has CI jobs in JJB:</strong> 134 Yes, 83 — (no JJB entry found)</p>
  <p><strong>Discovered by:</strong> gerrit (176), jjb (134), oom (58), relman (198)</p>
</div>

<div class="legend">
  <p><strong>How to read this table</strong></p>
  <p><em>Category</em> — <code>runtime</code> (deployed component), <code>build-dependency</code> (read-only, archived), <code>infrastructure</code> (e.g. OOM itself), <code>test</code>, <code>documentation</code>, <code>tooling</code>.</p>
  <p><em>Confidence</em> — <code>high</code> = image referenced in OOM Helm charts; <code>medium</code> = listed in relman <code>repos.yaml</code> or has CI jobs in JJB; <code>low</code> = heuristic discovery only.</p>
  <p><em>State</em> — Emoji indicator — see the State Legend below.</p>
  <p><em>Maintained</em> — From relman <code>repos.yaml</code> (<code>unmaintained: true</code> → <strong>No</strong>). <strong>Yes</strong> = explicitly listed and not flagged unmaintained; <strong>No</strong> = explicitly flagged unmaintained; <strong>—</strong> = no entry in <code>repos.yaml</code> (status unknown from this source).</p>
  <p><em>Has CI</em> — From the JJB collector scanning <code>ci-management</code>. <strong>Yes</strong> = at least one Jenkins job targets this repository; <strong>—</strong> = no JJB job was found (the collector does not record a definite <strong>No</strong>).</p>
</div>

<div class="state-legend">
  <p><strong>State Legend</strong></p>
  <p>✅ In current ONAP release</p>
  <p>☑️ Parent project (children in release)</p>
  <p>❌ Not in current ONAP release</p>
  <p>❓ Undetermined</p>
  <p>📦 Read-only / archived</p>
</div>

| Gerrit Project | Sources | Category | Confidence | State | Maintained | Has CI |
| -------------- | ------- | -------- | ---------- | ----- | ---------- | ------ |
| aai | gerrit, relman | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml">medium</abbr> | ☑️ | Yes | — |
| aai/aai-common | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ✅ | Yes | Yes |
| aai/babel | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ✅ | Yes | Yes |
| aai/graphadmin | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ✅ | Yes | Yes |
| aai/graphgraph | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| aai/logging-service | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| aai/model-loader | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ✅ | Yes | Yes |
| aai/oom | gerrit, relman | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| aai/resources | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ✅ | Yes | Yes |
| aai/rest-client | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| aai/schema-service | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ✅ | Yes | Yes |
| aai/sparky-be | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ✅ | Yes | Yes |
| aai/sparky-fe | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| aai/test-config | gerrit, relman | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Gerrit URL reference in OOM file aai/components/aai-sparky-be/values.yaml">medium</abbr> | ✅ | Yes | — |
| aai/traversal | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ✅ | Yes | Yes |
| ccsdk | gerrit, relman | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml">medium</abbr> | ☑️ | Yes | — |
| ccsdk/apps | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ✅ | Yes | Yes |
| ccsdk/cds | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ✅ | Yes | Yes |
| ccsdk/distribution | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ✅ | Yes | Yes |
| ccsdk/features | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| ccsdk/oran | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ✅ | Yes | Yes |
| ccsdk/parent | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| ccsdk/platform/blueprints | relman | runtime | <abbr title="Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| ccsdk/sli | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| ccsdk/storage/esaas | relman | runtime | <abbr title="Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| cli | relman | runtime | <abbr title="Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| cps | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ☑️ | Yes | Yes |
| cps/cps-tbdmt | relman | runtime | <abbr title="Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| cps/cps-temporal | relman | runtime | <abbr title="Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| cps/ncmp-dmi-plugin | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ✅ | Yes | Yes |
| dcaegen2 | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ☑️ | Yes | Yes |
| dcaegen2/analytics/tca-gen2 | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| dcaegen2/collectors/datafile | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| dcaegen2/collectors/hv-ves | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ✅ | Yes | Yes |
| dcaegen2/collectors/restconf | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| dcaegen2/collectors/snmptrap | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| dcaegen2/collectors/ves | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ✅ | Yes | Yes |
| dcaegen2/deployments | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ✅ | Yes | Yes |
| dcaegen2/platform | relman, jjb | runtime | <abbr title="Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ☑️ | Yes | Yes |
| dcaegen2/platform/blueprints | relman | runtime | <abbr title="Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| dcaegen2/platform/ves-openapi-manager | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ✅ | Yes | Yes |
| dcaegen2/services | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ☑️ | Yes | Yes |
| dcaegen2/services/heartbeat | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| dcaegen2/services/mapper | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| dcaegen2/services/pm-mapper | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| dcaegen2/services/prh | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ✅ | Yes | Yes |
| dcaegen2/services/sdk | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| dcaegen2/services/son-handler | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| dcaegen2/utils | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| demo | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB; Referenced in OOM file robot/values.yaml">medium</abbr> | ✅ | Yes | Yes |
| dmaap | gerrit, relman | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml">medium</abbr> | ☑️ | Yes | — |
| dmaap/buscontroller | gerrit, relman | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| dmaap/datarouter | oom, gerrit, relman | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml">high</abbr> | ✅ | Yes | — |
| dmaap/kafka11aaf | gerrit, relman | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| dmaap/messagerouter/dmaapclient | relman | runtime | <abbr title="Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| dmaap/messagerouter/messageservice | relman | runtime | <abbr title="Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| dmaap/zookeeper | relman | runtime | <abbr title="Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| doc | gerrit, relman | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| doc/doc-best-practice | gerrit | runtime | <abbr title="Discovered via Gerrit REST API">medium</abbr> | ❌ | — | — |
| holmes | gerrit, relman | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Referenced in OOM file onap/values.yaml">medium</abbr> | ☑️ | Yes | — |
| holmes/common | relman | runtime | <abbr title="Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| holmes/engine-management | relman | runtime | <abbr title="Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| holmes/rule-management | relman | runtime | <abbr title="Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| integration | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ☑️ | Yes | Yes |
| integration/csit | gerrit, relman | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| integration/data-provider | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| integration/docker/onap-java11 | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ✅ | Yes | Yes |
| integration/docker/onap-python | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| integration/gating | gerrit, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | — | Yes |
| integration/ietf-actn-tools | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| integration/onap-component-simulators | gerrit, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | — | Yes |
| integration/pipelines/build-integration | gerrit | runtime | <abbr title="Discovered via Gerrit REST API">medium</abbr> | ❌ | — | — |
| integration/pipelines/chained-ci | gerrit | runtime | <abbr title="Discovered via Gerrit REST API">medium</abbr> | ❌ | — | — |
| integration/pipelines/oom-automatic-installation | gerrit | runtime | <abbr title="Discovered via Gerrit REST API">medium</abbr> | ❌ | — | — |
| integration/pipelines/xtesting-onap | gerrit | runtime | <abbr title="Discovered via Gerrit REST API">medium</abbr> | ❌ | — | — |
| integration/python-onapsdk | gerrit, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | — | Yes |
| integration/seccom | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| integration/simulators/5G-core-nf-simulator | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| integration/simulators/A1-policy-enforcement-simulator | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| integration/simulators/core-nssmf-simulator | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| integration/simulators/nf-simulator | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| integration/simulators/nf-simulator/avcn-manager | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| integration/simulators/nf-simulator/netconf-server | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| integration/simulators/nf-simulator/pm-https-server | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| integration/simulators/nf-simulator/ves-client | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| integration/simulators/pnf-simulator | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| integration/simulators/ran-app | gerrit | runtime | <abbr title="Discovered via Gerrit REST API">medium</abbr> | ❌ | — | — |
| integration/simulators/ran-nssmf-simulator | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| integration/simulators/ran-simulator | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| integration/usecases/A1-policy-enforcement | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| integration/usecases/A1-policy-enforcement-r-apps | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| integration/xtesting | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| modeling/etsicatalog | relman | runtime | <abbr title="Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| modeling/modelspec | gerrit, relman | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| modeling/toscaparsers | relman | runtime | <abbr title="Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| msb | gerrit, relman | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| msb/apigateway | relman, jjb | runtime | <abbr title="Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| msb/discovery | relman, jjb | runtime | <abbr title="Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| msb/java-sdk | relman, jjb | runtime | <abbr title="Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| msb/service-mesh | gerrit, relman | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| msb/swagger-sdk | relman, jjb | runtime | <abbr title="Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| multicloud | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ☑️ | Yes | Yes |
| multicloud/framework | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ✅ | Yes | Yes |
| multicloud/k8s | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ✅ | Yes | Yes |
| multicloud/openstack | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ☑️ | Yes | Yes |
| multicloud/openstack/vmware | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| multicloud/openstack/windriver | gerrit, relman | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| oom | oom, gerrit, relman, jjb | infrastructure | <abbr title="OOM is the deployment repository; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ☑️ | Yes | Yes |
| oom/consul | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| oom/offline-installer | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| oom/platform/cert-manager | gerrit, relman | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| oom/platform/cert-service | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ✅ | Yes | Yes |
| oom/platform/keycloak | gerrit, relman | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| oom/readiness | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ✅ | Yes | Yes |
| oom/registrator | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| oom/utils | gerrit, relman | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| oparent | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| oparent/cia | gerrit, relman | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| optf | relman | runtime | <abbr title="Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| optf/has | relman | runtime | <abbr title="Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| optf/osdf | relman | runtime | <abbr title="Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| osa | gerrit, relman | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| policy | gerrit, relman | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml">medium</abbr> | ☑️ | Yes | — |
| policy/apex-pdp | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ✅ | Yes | Yes |
| policy/api | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ✅ | Yes | Yes |
| policy/clamp | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ✅ | Yes | Yes |
| policy/common | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| policy/distribution | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ✅ | Yes | Yes |
| policy/docker | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ✅ | Yes | Yes |
| policy/drools-applications | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| policy/drools-pdp | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ✅ | Yes | Yes |
| policy/gui | relman | runtime | <abbr title="Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| policy/models | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| policy/opa-pdp | oom, gerrit, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Has CI jobs in ci-management JJB">high</abbr> | ✅ | — | Yes |
| policy/pap | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ✅ | Yes | Yes |
| policy/parent | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| policy/xacml-pdp | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ✅ | Yes | Yes |
| portal-ng | gerrit | runtime | <abbr title="Discovered via Gerrit REST API; Referenced in OOM file onap/values.yaml">medium</abbr> | ✅ | — | — |
| portal-ng/bff | oom, gerrit, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Has CI jobs in ci-management JJB">high</abbr> | ✅ | — | Yes |
| portal-ng/e2e | gerrit | runtime | <abbr title="Discovered via Gerrit REST API">medium</abbr> | ❌ | — | — |
| portal-ng/history | oom, gerrit, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Has CI jobs in ci-management JJB">high</abbr> | ✅ | — | Yes |
| portal-ng/preferences | oom, gerrit, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Has CI jobs in ci-management JJB">high</abbr> | ✅ | — | Yes |
| portal-ng/ui | oom, gerrit, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Has CI jobs in ci-management JJB">high</abbr> | ✅ | — | Yes |
| relman | gerrit, relman | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| sandbox-2 | gerrit, relman | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| sandbox-3 | gerrit, relman | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| sdc | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ☑️ | Yes | Yes |
| sdc/onap-ui-angular | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| sdc/onap-ui-common | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| sdc/sdc-be-common | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| sdc/sdc-distribution-client | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| sdc/sdc-docker-base | gerrit, relman | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| sdc/sdc-helm-validator | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ✅ | Yes | Yes |
| sdc/sdc-pubsub | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| sdc/sdc-tosca | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| sdc/sdc-workflow-designer | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ✅ | Yes | Yes |
| sdnc | gerrit, relman | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml">medium</abbr> | ☑️ | Yes | — |
| sdnc/apps | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| sdnc/northbound | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| sdnc/oam | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ✅ | Yes | Yes |
| so | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ☑️ | Yes | Yes |
| so/adapters/so-cnf-adapter | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ✅ | Yes | Yes |
| so/adapters/so-etsi-sol003-adapter | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ✅ | Yes | Yes |
| so/adapters/so-etsi-sol005-adapter | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ✅ | Yes | Yes |
| so/adapters/so-nssmf-adapter | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ✅ | Yes | Yes |
| so/adapters/so-oof-adapter | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ✅ | Yes | Yes |
| so/chef-repo | gerrit, relman | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| so/docker-config | gerrit, relman | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Gerrit URL reference in OOM file so/components/so-mariadb/values.yaml">medium</abbr> | ✅ | Yes | — |
| so/libs | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| so/so-admin-cockpit | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ✅ | Yes | Yes |
| so/so-config | gerrit, relman | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| so/so-etsi-nfvo | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| spark-model-runner | relman | runtime | <abbr title="Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| testsuite | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ☑️ | Yes | Yes |
| testsuite/cds | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| testsuite/cds-mock-odl | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| testsuite/cds-mock-server | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| testsuite/cds-mock-ssh | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| testsuite/cds-modk-odl | jjb | runtime | <abbr title="Has CI jobs in ci-management JJB">medium</abbr> | ❓ | — | Yes |
| testsuite/oom | gerrit, relman | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| testsuite/python-testing-utils | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| testsuite/pythonsdk-tests | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| testsuite/robot-utils | gerrit, relman | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| university | gerrit, relman | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| usecase-ui | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ☑️ | Yes | Yes |
| usecase-ui/intent-analysis | oom, gerrit, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Has CI jobs in ci-management JJB">high</abbr> | ✅ | — | Yes |
| usecase-ui/llm-adaptation | oom, gerrit, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Has CI jobs in ci-management JJB">high</abbr> | ✅ | — | Yes |
| usecase-ui/nlp | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ✅ | Yes | Yes |
| usecase-ui/server | oom, gerrit, relman, jjb | runtime | <abbr title="Docker image referenced in OOM Helm charts; Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">high</abbr> | ✅ | Yes | Yes |
| vfc | gerrit, relman | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| vfc/gvnfm/vnflcm | relman | runtime | <abbr title="Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| vfc/gvnfm/vnfmgr | relman | runtime | <abbr title="Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| vfc/gvnfm/vnfres | relman | runtime | <abbr title="Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| vfc/nfvo/db | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| vfc/nfvo/driver/vnfm/gvnfm | relman | runtime | <abbr title="Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| vfc/nfvo/driver/vnfm/svnfm | relman | runtime | <abbr title="Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| vfc/nfvo/lcm | relman | runtime | <abbr title="Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| vnfrqts | gerrit, relman | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| vnfrqts/epics | gerrit, relman | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| vnfrqts/guidelines | gerrit, relman | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| vnfrqts/requirements | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| vnfrqts/testcases | gerrit, relman | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| vnfrqts/usecases | gerrit, relman | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| vnfsdk | gerrit, relman | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Referenced in OOM file onap/values.yaml">medium</abbr> | ☑️ | Yes | — |
| vnfsdk/dovetail-integration | relman | runtime | <abbr title="Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| vnfsdk/functest | relman | runtime | <abbr title="Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| vnfsdk/lctest | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| vnfsdk/model | gerrit, relman | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| vnfsdk/pkgtools | gerrit, relman, jjb | runtime | <abbr title="Discovered via Gerrit REST API; Listed in relman repos.yaml; Has CI jobs in ci-management JJB">medium</abbr> | ❌ | Yes | Yes |
| vnfsdk/refrepo | relman | runtime | <abbr title="Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| vnfsdk/validation | relman | runtime | <abbr title="Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| vvp | relman | runtime | <abbr title="Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| vvp/documentation | relman | runtime | <abbr title="Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| vvp/engagementmgr | relman | runtime | <abbr title="Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| vvp/regression-tests | relman | runtime | <abbr title="Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| vvp/test-engine | relman | runtime | <abbr title="Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |
| vvp/validation-scripts | relman | runtime | <abbr title="Listed in relman repos.yaml">medium</abbr> | ❌ | Yes | — |

### Totals

| Total | State | Description |
| ----: | :---: | ----------- |
| 54 | ✅ | In current ONAP release |
| 19 | ☑️ | Parent project (children in release) |
| 143 | ❌ | Not in current ONAP release |
| 1 | ❓ | Undetermined |

## Docker Images

<div class="summary">
  <p><strong>At a glance</strong></p>
  <p><strong>Total images:</strong> 89</p>
  <p><strong>By attribution:</strong> 88 override, 1 leaf-match, 0 heuristic, 0 unresolved</p>
  <p><strong>Verified against Gerrit:</strong> 88 ✓, 1 ✗, 0 — (no ground truth)</p>
  <p><strong>Validated in Nexus:</strong> 89 Yes, 0 No, 0 — (not probed)</p>
</div>

<div class="legend">
  <p><strong>How to read this table</strong></p>
  <p><em>Validated</em> — <strong>Yes</strong> = image:tag confirmed present in Nexus; <strong>No</strong> = lookup failed; <strong>—</strong> = no Nexus probe was attempted.</p>
  <p><em>Attribution</em> — How the image was mapped to a Gerrit project. See the Attribution key below for the full list of reason codes and verification markers.</p>
</div>

<div class="legend">
  <p><strong>Attribution key</strong></p>
  <p><em>override</em> — Explicit entry in <code>image_repo_mapping.yaml</code>.</p>
  <p><em>override-stale</em> — Explicit override exists but resolves to a project not in Gerrit (mapping file is out of date).</p>
  <p><em>leaf-match-namespace</em> — Longest-match on the image's leaf segment within the same top-level namespace (best-quality automatic match).</p>
  <p><em>leaf-match-cross-namespace</em> — Same as above but the match crossed namespaces — flagged for human review.</p>
  <p><em>heuristic-*-verified</em> — Pattern-based guess (<code>org.onap.*</code> prefix, dash→slash, or slash passthrough) that was confirmed against the Gerrit project list.</p>
  <p><em>heuristic-*-unverified</em> — Same heuristic, but no Gerrit confirmation — lower-confidence result.</p>
  <p><em>unresolved</em> — Mapper found no candidate; no Gerrit project assigned.</p>
  <p><em>✓ / ✗ / (blank)</em> — Verification marker: <strong>✓</strong> = confirmed in Gerrit ground truth; <strong>✗</strong> = could not be verified; blank = no Gerrit ground truth was loaded for this run.</p>
  <p><em>(alt: …)</em> — Other plausible candidates the longest-match algorithm considered but did not choose.</p>
</div>

| Image | Tag | Gerrit Project | Registry | Validated | Attribution |
| ----- | --- | -------------- | -------- | --------- | ----------- |
| onap/aai-graphadmin | 1.16.0 | aai/graphadmin | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/aai-haproxy | 1.15.2 | aai/aai-common | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/aai-resources | 1.16.0 | aai/resources | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/aai-schema-service | 1.12.11 | aai/schema-service | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/aai-traversal | 1.16.0 | aai/traversal | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/babel | 1.13.5 | aai/babel | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/ccsdk-apps-ms-neng | 1.4.0 | ccsdk/apps | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/ccsdk-blueprintsprocessor | 1.10.0 | ccsdk/cds | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/ccsdk-cds-ui-server | 1.10.0 | ccsdk/cds | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/ccsdk-commandexecutor | 1.10.0 | ccsdk/cds | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/ccsdk-dgbuilder-image | 2.2.0 | ccsdk/distribution | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/ccsdk-oran-a1policymanagementservice | 2.2.0 | ccsdk/oran | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/ccsdk-py-executor | 1.10.0 | ccsdk/cds | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/ccsdk-sdclistener | 1.10.0 | ccsdk/cds | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/cps-and-ncmp | 3.7.0 | cps | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/cps-temporal | 1.2.1 | cps | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/dmaap/datarouter-prov-client | 2.1.15 | dmaap/datarouter | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/integration-java11 | 10.0.0 | integration/docker/onap-java11 | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/model-loader | 1.14.3 | aai/model-loader | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/multicloud/framework | 1.9.2 | multicloud/framework | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/multicloud/framework-artifactbroker | 1.9.3 | multicloud/framework | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/multicloud/k8s | 0.12.0 | multicloud/k8s | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/multicloud/openstack-fcaps | 1.5.7 | multicloud/openstack | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/music/prom | 1.0.5 | music/prom | nexus3.onap.org:10001 | Yes | override-stale ✗ |
| onap/ncmp-dmi-plugin | 1.7.0 | cps/ncmp-dmi-plugin | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/oom/readiness | 7.0.1 | oom/readiness | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/org.onap.dcaegen2.collectors.hv-ves.hv-collector-main | 1.11.1 | dcaegen2/collectors/hv-ves | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/org.onap.dcaegen2.collectors.ves.vescollector | 1.12.6 | dcaegen2/collectors/ves | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/org.onap.dcaegen2.deployments.dcae-services-policy-sync | 1.0.1 | dcaegen2/deployments | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/org.onap.dcaegen2.deployments.healthcheck-container | 2.4.1 | dcaegen2/deployments | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/org.onap.dcaegen2.platform.ves-openapi-manager | 1.3.1 | dcaegen2/platform/ves-openapi-manager | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/org.onap.dcaegen2.services.datalake.exposure.service | 1.1.3 | dcaegen2/services | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/org.onap.dcaegen2.services.datalakeadminui | 1.1.3 | dcaegen2/services | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/org.onap.dcaegen2.services.datalakefeeder | 1.2.0 | dcaegen2/services | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/org.onap.dcaegen2.services.prh.prh-app-server | 1.12.0 | dcaegen2/services/prh | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/org.onap.oom.platform.cert-service.oom-certservice-api | 2.6.0 | oom/platform/cert-service | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/org.onap.oom.platform.cert-service.oom-certservice-k8s-external-provider | 2.6.0 | oom/platform/cert-service | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/policy-apex-pdp | 4.2.2 | policy/apex-pdp | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/policy-api | 4.2.2 | policy/api | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/policy-clamp-ac-a1pms-ppnt | 9.0.0 | policy/clamp | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/policy-clamp-ac-http-ppnt | 9.0.0 | policy/clamp | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/policy-clamp-ac-k8s-ppnt | 8.2.2 | policy/clamp | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/policy-clamp-ac-kserve-ppnt | 9.0.0 | policy/clamp | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/policy-clamp-ac-pf-ppnt | 9.0.0 | policy/clamp | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/policy-clamp-runtime-acm | 8.2.2 | policy/clamp | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/policy-db-migrator | 4.2.2 | policy/docker | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/policy-distribution | 4.2.2 | policy/distribution | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/policy-opa-pdp | 1.0.8 | policy/opa-pdp | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/policy-pap | 4.2.2 | policy/pap | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/policy-pdpd-cl | 3.2.2 | policy/drools-pdp | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/policy-xacml-pdp | 4.2.2 | policy/xacml-pdp | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/portal-ng/bff | latest | portal-ng/bff | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/portal-ng/history | latest | portal-ng/history | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/portal-ng/preferences | latest | portal-ng/preferences | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/portal-ng/ui | latest | portal-ng/ui | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/sdc-backend-all-plugins | 1.16.2 | sdc | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/sdc-cassandra | 1.16.2 | sdc | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/sdc-frontend | 1.16.2 | sdc | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/sdc-helm-validator | 1.3.3 | sdc/sdc-helm-validator | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/sdc-onboard-backend | 1.16.2 | sdc | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/sdc-workflow-backend | 1.14.1 | sdc/sdc-workflow-designer | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/sdc-workflow-frontend | 1.14.1 | sdc/sdc-workflow-designer | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/sdnc-ansible-server-image | 3.2.4 | sdnc/oam | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/sdnc-image | 3.2.4 | sdnc/oam | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/sdnc-ueb-listener-image | 3.2.4 | sdnc/oam | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/sdnc-web-image | 3.2.4 | sdnc/oam | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/so/api-handler-infra | 1.18.0 | so | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/so/bpmn-infra | 1.18.0 | so | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/so/catalog-db-adapter | 1.18.0 | so | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/so/openstack-adapter | 1.18.0-20260413T1353 | so | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/so/request-db-adapter | 1.18.0 | so | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/so/sdc-controller | 1.18.0 | so | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/so/sdnc-adapter | 1.18.0 | so | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/so/so-admin-cockpit | 1.10.0 | so/so-admin-cockpit | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/so/so-cnf-adapter | 1.14.0 | so/adapters/so-cnf-adapter | nexus3.onap.org:10001 | Yes | leaf-match-namespace ✓ |
| onap/so/so-cnfm-as-lcm | 1.14.0 | so | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/so/so-etsi-nfvo-ns-lcm | 1.10.0 | so | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/so/so-etsi-sol003-adapter | 1.10.0 | so/adapters/so-etsi-sol003-adapter | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/so/so-etsi-sol005-adapter | 1.10.0 | so/adapters/so-etsi-sol005-adapter | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/so/so-nssmf-adapter | 1.12.0 | so/adapters/so-nssmf-adapter | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/so/so-oof-adapter | 1.11.0 | so/adapters/so-oof-adapter | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/so/ve-vnfm-adapter | 1.6.4 | so | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/sparky-be | 2.1.0 | aai/sparky-be | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/testsuite | 1.14.0 | testsuite | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/usecase-ui | 16.0.1 | usecase-ui | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/usecase-ui-intent-analysis | 16.0.1 | usecase-ui/intent-analysis | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/usecase-ui-llm-adaptation | 16.0.1 | usecase-ui/llm-adaptation | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/usecase-ui-nlp | 1.0.5 | usecase-ui/nlp | nexus3.onap.org:10001 | Yes | override ✓ |
| onap/usecase-ui-server | 16.0.1 | usecase-ui/server | nexus3.onap.org:10001 | Yes | override ✓ |

## Helm Components

<div class="summary">
  <p><strong>At a glance</strong></p>
  <p><strong>Total components:</strong> 98</p>
  <p><strong>Enabled by default:</strong> 0 Yes, 16 No, 82 —</p>
  <p><strong>With Helm condition key:</strong> 16 of 98</p>
</div>

<div class="legend">
  <p><strong>How to read this table</strong></p>
  <p><em>Enabled by default</em> — Whether the component is deployed when the umbrella chart is installed without overrides. <strong>Yes</strong> / <strong>No</strong> reflect the <code>&lt;component&gt;.enabled</code> default in the OOM umbrella <code>values.yaml</code>; <strong>—</strong> means no <code>enabled</code> key was present (Helm treats this as unconditional). <strong>Note:</strong> ONAP's umbrella chart is opt-in — most components default to <strong>No</strong>, and operators select the ones they want at install time.</p>
  <p><em>(via <code>….enabled</code>)</em> — Helm <em>dependency condition</em> from the umbrella <code>Chart.yaml</code> — the values path operators set to <code>true</code> to include this subchart in a deployment.</p>
</div>

| Name | Version | Enabled by default |
| ---- | ------- | ------------------ |
| a1policymanagement | ~13.x-0 | No (via `a1policymanagement.enabled`) |
| aai | ~16.x-0 | No (via `aai.enabled`) |
| aai-babel | 15.0.2 | — |
| aai-graphadmin | 16.0.0 | — |
| aai-modelloader | 15.0.5 | — |
| aai-resources | 16.0.0 | — |
| aai-schema-service | 16.0.0 | — |
| aai-sparky-be | 16.0.0 | — |
| aai-traversal | 16.0.0 | — |
| authentication | ~15.x-0 | No (via `authentication.enabled`) |
| cds | ~17.x-0 | No (via `cds.enabled`) |
| cds-blueprints-processor | 13.0.1 | — |
| cds-command-executor | 13.0.0 | — |
| cds-py-executor | 13.0.0 | — |
| cds-sdc-listener | 13.0.0 | — |
| cds-ui | 13.0.0 | — |
| chartmuseum | 13.0.0 | — |
| cmpv2-cert-provider | 13.0.0 | — |
| cps | ~13.x-0 | No (via `cps.enabled`) |
| cps-core | 13.0.2 | — |
| cps-temporal | 13.0.1 | — |
| dcae-datalake-admin-ui | 13.0.1 | — |
| dcae-datalake-des | 13.0.1 | — |
| dcae-datalake-feeder | 13.0.1 | — |
| dcae-hv-ves-collector | 13.0.0 | — |
| dcae-ms-healthcheck | 13.0.0 | — |
| dcae-prh | 14.0.0 | — |
| dcae-ves-collector | 13.1.1 | — |
| dcae-ves-openapi-manager | 13.0.0 | — |
| dcaegen2-services | ~16.x-0 | No (via `dcaegen2-services.enabled`) |
| dgbuilder | 15.1.0 | — |
| multicloud | ~15.x-0 | No (via `multicloud.enabled`) |
| multicloud-fcaps | 13.0.0 | — |
| multicloud-k8s | 13.3.0 | — |
| ncmp-dmi-plugin | 13.0.1 | — |
| network-name-gen | 16.0.0 | — |
| onap-keycloak-config-cli | 6.2.1 | — |
| oom-cert-service | 13.0.0 | — |
| platform | ~13.x-0 | No (via `platform.enabled`) |
| policy | ~17.x-0 | No (via `policy.enabled`) |
| policy-apex-pdp | 17.0.0 | — |
| policy-api | 17.0.0 | — |
| policy-clamp-ac-a1pms-ppnt | 17.0.1 | — |
| policy-clamp-ac-http-ppnt | 17.0.1 | — |
| policy-clamp-ac-k8s-ppnt | 17.0.0 | — |
| policy-clamp-ac-kserve-ppnt | 17.0.1 | — |
| policy-clamp-ac-pf-ppnt | 17.0.1 | — |
| policy-clamp-runtime-acm | 17.0.0 | — |
| policy-distribution | 17.0.0 | — |
| policy-drools-pdp | 17.0.0 | — |
| policy-nexus | 17.0.0 | — |
| policy-opa-pdp | 17.0.0 | — |
| policy-pap | 17.0.0 | — |
| policy-xacml-pdp | 17.0.0 | — |
| portal-ng | ~14.x-0 | No (via `portal-ng.enabled`) |
| portal-ng-bff | 13.1.1 | — |
| portal-ng-history | 14.1.1 | — |
| portal-ng-preferences | 14.1.1 | — |
| portal-ng-ui | 13.0.1 | — |
| robot | ~13.x-0 | No (via `robot.enabled`) |
| sdc | ~13.x-0 | No (via `sdc.enabled`) |
| sdc-be | 13.0.5 | — |
| sdc-cs | 13.0.5 | — |
| sdc-fe | 13.0.4 | — |
| sdc-helm-validator | 13.0.1 | — |
| sdc-onboarding-be | 13.0.5 | — |
| sdc-wfd-be | 13.0.5 | — |
| sdc-wfd-fe | 13.0.4 | — |
| sdnc | ~16.x-0 | No (via `sdnc.enabled`) |
| sdnc-ansible-server | 15.1.0 | — |
| sdnc-prom | 13.0.0 | — |
| sdnc-web | 15.1.0 | — |
| so | ~17.x-0 | No (via `so.enabled`) |
| so-admin-cockpit | 15.0.0 | — |
| so-bpmn-infra | 17.0.0 | — |
| so-catalog-db-adapter | 17.0.0 | — |
| so-cnf-adapter | 15.0.1 | — |
| so-cnfm-lcm | 13.0.0 | — |
| so-etsi-nfvo-ns-lcm | 13.0.0 | — |
| so-etsi-sol003-adapter | 13.0.0 | — |
| so-etsi-sol005-adapter | 13.0.0 | — |
| so-mariadb | 16.0.0 | — |
| so-nssmf-adapter | 15.0.0 | — |
| so-oof-adapter | 15.0.0 | — |
| so-openstack-adapter | 17.0.0 | — |
| so-request-db-adapter | 17.0.0 | — |
| so-sdc-controller | 17.0.0 | — |
| so-sdnc-adapter | 17.0.0 | — |
| so-ve-vnfm-adapter | 13.0.0 | — |
| soHelpers | 13.0.1 | — |
| strimzi | ~16.x-0 | No (via `strimzi.enabled`) |
| strimzi-kafka-bridge | 13.0.3 | — |
| ueb-listener | 15.1.0 | — |
| uui | ~16.x-0 | No (via `uui.enabled`) |
| uui-intent-analysis | 16.0.1 | — |
| uui-llm-adaptation | 16.0.1 | — |
| uui-nlp | 13.0.0 | — |
| uui-server | 16.0.1 | — |
