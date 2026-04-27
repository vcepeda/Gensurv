<template>
  <li class="tree-node-item">
    <template v-if="isDirectory">
      <button class="tree-dir-btn" type="button" @click="expanded = !expanded">
        <span class="tree-caret">{{ expanded ? "▾" : "▸" }}</span>
        <span>{{ node.name }}</span>
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
import { computed, ref } from "vue";

defineOptions({ name: "ResultTreeNode" });

const props = defineProps({
  node: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(["select-file"]);

const isDirectory = computed(() => props.node?.type === "directory");
const expanded = ref(true);
</script>

<style scoped>
.tree-node-item {
  list-style: none;
  margin: 0.15rem 0;
}

.tree-dir-btn {
  background: transparent;
  border: 0;
  padding: 0.2rem 0.3rem;
  cursor: pointer;
  text-align: left;
  color: #1f2937;
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
