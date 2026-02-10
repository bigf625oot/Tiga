<template>
    <div class="space-y-4">
        <div v-if="isLoading" class="flex justify-center py-4">
            <span class="text-slate-400 text-sm">加载技能库...</span>
        </div>
        
        <div v-else-if="skills.length === 0" class="text-center py-8 border border-dashed border-slate-200 rounded-lg bg-slate-50">
            <div class="text-slate-400 text-sm">暂无可用技能</div>
            <div class="text-slate-300 text-xs mt-1">请联系管理员添加技能</div>
        </div>

        <div v-else class="grid grid-cols-1 gap-3">
            <div 
                v-for="skill in skills" 
                :key="skill.id"
                class="flex items-start gap-3 p-3 border rounded-lg cursor-pointer transition-all group"
                :class="isSelected(skill.id) ? 'border-blue-500 bg-blue-50/30' : 'border-slate-200 hover:border-blue-300 hover:bg-slate-50'"
                @click="toggleSkill(skill.id)"
            >
                <div class="pt-0.5">
                    <input 
                        type="checkbox" 
                        :checked="isSelected(skill.id)" 
                        class="rounded text-blue-600 focus:ring-blue-500 pointer-events-none"
                    >
                </div>
                <div class="flex-1">
                    <div class="flex items-center justify-between">
                        <span class="text-sm font-medium text-slate-800">{{ skill.name }}</span>
                        <span class="text-xs px-1.5 py-0.5 bg-slate-100 text-slate-500 rounded border border-slate-200">v{{ skill.version }}</span>
                    </div>
                    <p class="text-xs text-slate-500 mt-1 line-clamp-2 leading-relaxed">
                        {{ skill.description || '暂无描述' }}
                    </p>
                    
                    <!-- Metadata tags if any -->
                    <div v-if="skill.meta_data && skill.meta_data.tags" class="flex flex-wrap gap-1 mt-2">
                        <span v-for="tag in skill.meta_data.tags" :key="tag" class="text-[10px] px-1.5 py-0.5 bg-white border border-slate-100 rounded-full text-slate-400">
                            #{{ tag }}
                        </span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const props = defineProps({
    modelValue: {
        type: Array,
        default: () => []
    }
});

const emit = defineEmits(['update:modelValue']);

const skills = ref([]);
const isLoading = ref(true);

const fetchSkills = async () => {
    isLoading.value = true;
    try {
        const res = await fetch('/api/v1/skills/');
        if (res.ok) {
            skills.value = await res.json();
        }
    } catch (e) {
        console.error("Failed to fetch skills", e);
    } finally {
        isLoading.value = false;
    }
};

const isSelected = (id) => {
    return props.modelValue.includes(id);
};

const toggleSkill = (id) => {
    const newValue = [...props.modelValue];
    const index = newValue.indexOf(id);
    if (index === -1) {
        newValue.push(id);
    } else {
        newValue.splice(index, 1);
    }
    emit('update:modelValue', newValue);
};

onMounted(() => {
    fetchSkills();
});
</script>
