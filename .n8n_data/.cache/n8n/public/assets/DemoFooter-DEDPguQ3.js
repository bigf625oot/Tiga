import { C as computed, E as createCommentVNode, P as defineComponent, T as createBlock, et as openBlock } from "./vue.runtime.esm-bundler-tP5dCd7J.js";
import "./_MapCache-BMHbvJCZ.js";
import "./src-DqmLIEAl.js";
import "./en-CF30SCh2.js";
import "./preload-helper-CR0ecmWK.js";
import "./_plugin-vue_export-helper-BwBpWJRZ.js";
import "./truncate-B1pKLfYW.js";
import { N as useWorkflowsStore } from "./builder.store-D03YeWV5.js";
import "./empty-BuGRxzl4.js";
import "./sanitize-html-Cc45ZKm8.js";
import "./CalendarDate-zWqgZMlk.js";
import "./path-browserify-BtCDmZ3_.js";
import "./constants-D62txg5e.js";
import "./merge-CY7KXArB.js";
import "./_baseOrderBy-DhDCVDnK.js";
import "./dateformat-CM9k0--B.js";
import "./useDebounce-CfSDWjpl.js";
import "./assistant.store-DKBbr3mA.js";
import "./chatPanel.store-BDqyoUvy.js";
import "./retry-dP46utx2.js";
import "./executions.store-CKuwjXt_.js";
import "./useRunWorkflow-526gGsiD.js";
import "./usePinnedData-DXKvbgNr.js";
import "./nodeCreator.store-CpwSg-PB.js";
import "./nodeIcon-Bq6ImsWM.js";
import "./useClipboard-CuFR0Oza.js";
import "./useCanvasOperations-Cj5EHXV0.js";
import { t as LogsPanel_default } from "./LogsPanel-CmJfMJc2.js";
import "./folders.store-CzHexdK7.js";
import "./NodeIcon-CCjrGhsr.js";
import "./KeyboardShortcutTooltip-NmJhkpDl.js";
import "./isEmpty-BuyrzhgL.js";
import "./NDVEmptyState-CFcIB3lC.js";
import "./externalSecrets.ee.store-DQNBRTAv.js";
import "./uniqBy-Dkms4n6p.js";
import "./RunDataHtml-CkjC7YuF.js";
import "./VueMarkdown-BZruDYY0.js";
import "./schemaPreview.store-CBZCG29q.js";
import "./vue-json-pretty-DGKuDe33.js";
import "./dateFormatter-Dqzt2wPY.js";
import "./useExecutionHelpers-v2Eu_GJa.js";
import "./useKeybindings-DKs2DRdy.js";
import "./fileUtils-D_SiS8no.js";
import "./core-6W4wWNc1.js";
import "./ChatFile-cnNK8Kf8.js";
import "./xml-B6veOr9z.js";
import "./AnimatedSpinner-wiGFgffA.js";
import "./useLogsTreeExpand-DF4zHms3.js";
import "./core-BbiIkN91.js";
var DemoFooter_default = /* @__PURE__ */ defineComponent({
	__name: "DemoFooter",
	setup(__props) {
		const workflowsStore = useWorkflowsStore();
		const hasExecutionData = computed(() => workflowsStore.workflowExecutionData);
		return (_ctx, _cache) => {
			return hasExecutionData.value ? (openBlock(), createBlock(LogsPanel_default, {
				key: 0,
				"is-read-only": true
			})) : createCommentVNode("", true);
		};
	}
});
export { DemoFooter_default as default };
