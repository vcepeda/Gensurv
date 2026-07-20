<template>
  <li class="tree-node-item">
    <template v-if="isDirectory">
      <button class="tree-dir-btn" type="button" @click="expanded = !expanded">
        <span class="tree-caret">{{ expanded ? "▾" : "▸" }}</span>
        <span>{{ node.name }}</span>
        <span
          v-if="description"
          ref="infoIconRef"
          class="tree-info-icon"
          data-bs-toggle="tooltip"
          data-bs-placement="right"
          :title="description"
          @click.stop
        >i</span>
      </button>

      <ul v-if="expanded" class="tree-children">
        <ResultTreeNode
          v-for="child in node.children || []"
          :key="child.path"
          :node="child"
          @select-file="emit('select-file', $event)"
        />
      </ul>
    </template>

    <template v-else>
      <a href="#" class="tree-file-link" @click.prevent="emit('select-file', node)">
        {{ node.name }}
      </a>
    </template>
  </li>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { Tooltip } from "bootstrap";

defineOptions({ name: "ResultTreeNode" });

const props = defineProps({
  node: {
    type: Object,
    required: true,
  },
  defaultExpanded: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["select-file"]);

// One-sentence descriptions of each Bactopia pipeline stage, keyed by result folder name.
// See https://bactopia.io/full-guide
const STAGE_DESCRIPTIONS = {
  gather: "Collects all the raw sequencing data in one place, downloading samples from ENA/SRA or NCBI as needed.",
  qc: "Performs quality control on the raw reads, assessing and filtering out poor-quality data.",
  assembler: "Assembles the quality-controlled reads into contigs.",
  annotator: "Annotates the assembled contigs, identifying genes, proteins, rRNA, and tRNA.",
  sketcher: "Creates genomic sketches of the contigs and queries reference databases for rapid taxonomic classification.",
  mlst: "Determines the sequence type of the assembly by scanning it against PubMLST typing schemes.",
  amrfinderplus: "Identifies antibiotic resistance genes and mutations in the contigs and proteins.",
  merlin: "Automatically runs species-specific typing tools based on the sample's taxonomic classification.",
};

const isDirectory = computed(() => props.node?.type === "directory");
const expanded = ref(props.defaultExpanded);
const description = computed(() => STAGE_DESCRIPTIONS[props.node?.name?.toLowerCase()] || "");

const infoIconRef = ref(null);
let tooltipInstance = null;

onMounted(() => {
  if (infoIconRef.value) {
    tooltipInstance = new Tooltip(infoIconRef.value);
  }
});

onBeforeUnmount(() => {
  tooltipInstance?.dispose();
});
</script>

<style scoped>
.tree-node-item {
  list-style: none;
  margin: 0.15rem 0;
}

.tree-dir-btn {
  display: inline-flex;
  align-items: center;
  background: transparent;
  border: 0;
  padding: 0.2rem 0.3rem;
  cursor: pointer;
  text-align: left;
  color: #1f2937;
}

.tree-info-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1rem;
  height: 1rem;
  margin-left: 0.4rem;
  border: 1px solid #6b7280;
  border-radius: 50%;
  color: #6b7280;
  font-size: 0.65rem;
  font-style: italic;
  font-weight: 600;
  line-height: 1;
  cursor: pointer;
  flex-shrink: 0;
}

.tree-caret {
  display: inline-block;
  width: 2rem;
  font-size: 2rem;
  line-height: 1;
  color: #6b7280;
}

.tree-children {
  margin: 0.15rem 0 0.2rem 1rem;
  padding: 0;
}

.tree-file-link {
  display: inline-block;
  padding: 0.2rem 0.3rem;
  color: #1d4ed8;
  text-decoration: none;
}

.tree-file-link:hover {
  text-decoration: underline;
}
</style>
