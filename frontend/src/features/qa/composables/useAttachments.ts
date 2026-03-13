import { ref, computed, watch } from 'vue';
import { refDebounced } from '@vueuse/core';
import { knowledgeService } from '../services/knowledgeService';
import { useToast } from '@/components/ui/toast/use-toast';
import { MAX_FILE_SIZE_MB, ACCEPTED_FILE_TYPES } from '../constants';
import type { Attachment, KnowledgeDoc } from '../types';

/**
 * Manages file uploads (local and knowledge base) and attachment selection.
 * 
 * @returns Attachment state and management functions
 */
export function useAttachments() {
  const { toast } = useToast();
  const attachmentModalVisible = ref(false);
  const activeAttachmentTab = ref('local');
  const localFileList = ref<File[]>([]);
  const knowledgeDocs = ref<KnowledgeDoc[]>([]);
  const searchSuggestions = ref<string[]>([]);
  const selectedKnowledgeRowKeys = ref<string[]>([]);
  const knowledgeSearchKeyword = ref('');
  const debouncedKeyword = refDebounced(knowledgeSearchKeyword, 300);
  
  // Watch for keyword changes to trigger search (debounced)
  watch(debouncedKeyword, (newVal) => {
    // Fetch suggestions while user is typing
    if (newVal) {
      fetchSuggestions(newVal);
    }
    // Auto-search after typing stops
    fetchKnowledgeDocs(undefined, newVal);
  });

  const knowledgeLoading = ref(false);
  const selectedAttachments = ref<Attachment[]>([]);

  const fetchKnowledgeDocs = async (currentAgentConfig?: any, keyword?: string) => {
    knowledgeLoading.value = true;
    try {
      let docs = await knowledgeService.getKnowledgeDocs(keyword);
      if (currentAgentConfig?.document_ids?.length > 0) {
        docs = docs.filter(d => currentAgentConfig.document_ids.includes(d.id));
      }
      knowledgeDocs.value = docs;
    } catch (e) {
      console.error(e);
      toast({ description: '获取知识库文档出错', variant: 'destructive' });
    } finally {
      knowledgeLoading.value = false;
    }
  };

  const fetchSuggestions = async (keyword: string) => {
    if (!keyword) {
      searchSuggestions.value = [];
      return;
    }
    try {
      // Reuse the search API but maybe limit results or just take top 5
      const docs = await knowledgeService.getKnowledgeDocs(keyword);
      // We only want filenames
      searchSuggestions.value = docs.slice(0, 5).map(d => d.filename);
    } catch (e) {
      console.error(e);
    }
  };

  const handleLocalUpload = (file: File) => {
    const isLtMax = file.size / 1024 / 1024 < MAX_FILE_SIZE_MB;
    if (!isLtMax) {
      toast({ description: `文件大小不能超过 ${MAX_FILE_SIZE_MB}MB!`, variant: 'destructive' });
      return false;
    }
    const fileExt = file.name.slice(file.name.lastIndexOf('.')).toLowerCase();
    if (!ACCEPTED_FILE_TYPES.includes(fileExt)) {
      toast({ description: '不支持的文件类型!', variant: 'destructive' });
      return false;
    }
    localFileList.value = [...localFileList.value, file];
    return false;
  };

  const removeLocalFile = (file: File) => {
    const index = localFileList.value.indexOf(file);
    if (index > -1) {
        const newFileList = localFileList.value.slice();
        newFileList.splice(index, 1);
        localFileList.value = newFileList;
    }
  };

  const handleAttachmentOk = () => {
    const localAtts: Attachment[] = localFileList.value.map(f => ({
      type: 'local',
      name: f.name,
      size: f.size,
      file: f
    }));
    const knowledgeAtts: Attachment[] = knowledgeDocs.value
      .filter(d => selectedKnowledgeRowKeys.value.includes(d.id))
      .map(d => ({
        type: 'knowledge',
        name: d.filename,
        size: d.file_size,
        id: d.id
      }));
    
    selectedAttachments.value = [...localAtts, ...knowledgeAtts];
    attachmentModalVisible.value = false;
    toast({ description: `已选择 ${selectedAttachments.value.length} 个附件` });
  };

  const removeAttachment = (attachmentOrIndex: number | Attachment) => {
    if (typeof attachmentOrIndex === 'number') {
        selectedAttachments.value.splice(attachmentOrIndex, 1);
    } else {
        const index = selectedAttachments.value.indexOf(attachmentOrIndex);
        if (index > -1) {
            selectedAttachments.value.splice(index, 1);
        }
    }
  };

  const addLocalAttachments = (files: File[]) => {
    const validFiles: File[] = [];
    files.forEach(file => {
        const isLtMax = file.size / 1024 / 1024 < MAX_FILE_SIZE_MB;
        if (!isLtMax) {
          toast({ description: `文件 ${file.name} 大小超过 ${MAX_FILE_SIZE_MB}MB 限制!`, variant: 'destructive' });
          return;
        }
        const fileExt = file.name.slice(file.name.lastIndexOf('.')).toLowerCase();
        if (!ACCEPTED_FILE_TYPES.includes(fileExt)) {
           toast({ description: `不支持的文件类型: ${file.name}`, variant: 'destructive' });
           return;
        }
        validFiles.push(file);
    });

    if (validFiles.length > 0) {
        const newAtts: Attachment[] = validFiles.map(f => ({
          type: 'local',
          name: f.name,
          size: f.size,
          file: f
        }));
        localFileList.value = [...localFileList.value, ...validFiles];
        selectedAttachments.value = [...selectedAttachments.value, ...newAtts];
    }
  };

  const filteredKnowledgeDocs = computed(() => {
    return knowledgeDocs.value;
  });

  return {
    attachmentModalVisible,
    activeAttachmentTab,
    localFileList,
    knowledgeDocs,
    searchSuggestions,
    selectedKnowledgeRowKeys,
    knowledgeSearchKeyword,
    knowledgeLoading,
    selectedAttachments,
    fetchKnowledgeDocs,
    fetchSuggestions,
    handleLocalUpload,
    removeLocalFile,
    handleAttachmentOk,
    removeAttachment,
    addLocalAttachments,
    filteredKnowledgeDocs
  };
}
