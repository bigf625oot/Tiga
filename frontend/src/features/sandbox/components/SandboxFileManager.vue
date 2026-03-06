<template>
  <div class="h-full flex flex-col bg-white rounded-lg shadow-sm border border-slate-200">
    <div class="p-3 border-b border-slate-100 flex justify-between items-center bg-slate-50 rounded-t-lg">
      <h3 class="text-sm font-bold text-slate-700 flex items-center">
        <FolderOpenOutlined class="mr-2" /> 文件管理
      </h3>
      <div class="flex gap-2">
         <button class="p-1 hover:bg-slate-200 rounded transition-colors text-slate-500" title="Refresh">
            <ReloadOutlined />
         </button>
         <button class="p-1 hover:bg-slate-200 rounded transition-colors text-slate-500" title="Upload">
            <CloudUploadOutlined />
         </button>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto p-2 custom-scrollbar">
        <!-- Breadcrumb (Mock) -->
        <div class="text-xs text-slate-500 mb-2 px-2">/ workspace / project</div>

        <ul class="space-y-1">
            <li v-for="file in files" :key="file.path" 
                class="flex items-center p-2 rounded hover:bg-slate-100 cursor-pointer group text-sm transition-colors">
                <component :is="getFileIcon(file.type)" class="mr-2 text-slate-400" />
                <span class="flex-1 truncate text-slate-700">{{ file.name }}</span>
                <span class="text-xs text-slate-400 mr-2">{{ file.size }}</span>
                
                <div class="opacity-0 group-hover:opacity-100 flex gap-1">
                    <button class="text-slate-400 hover:text-blue-500 p-1" title="Download">
                        <DownloadOutlined />
                    </button>
                    <button class="text-slate-400 hover:text-red-500 p-1" title="Delete">
                        <DeleteOutlined />
                    </button>
                </div>
            </li>
        </ul>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { 
    FolderOpenOutlined, 
    FileOutlined, 
    FileTextOutlined, 
    FileImageOutlined,
    ReloadOutlined,
    CloudUploadOutlined,
    DownloadOutlined,
    DeleteOutlined
} from '@ant-design/icons-vue';

const files = ref([
    { name: 'main.py', type: 'code', size: '2.1KB', path: '/main.py' },
    { name: 'requirements.txt', type: 'text', size: '120B', path: '/requirements.txt' },
    { name: 'data', type: 'folder', size: '-', path: '/data' },
    { name: 'output.png', type: 'image', size: '1.2MB', path: '/output.png' },
    { name: 'logs', type: 'folder', size: '-', path: '/logs' },
]);

const getFileIcon = (type) => {
    switch (type) {
        case 'folder': return FolderOpenOutlined;
        case 'image': return FileImageOutlined;
        case 'code': return FileTextOutlined; // Or specific code icon
        default: return FileOutlined;
    }
};
</script>
