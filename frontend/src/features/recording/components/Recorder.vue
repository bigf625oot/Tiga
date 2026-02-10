<template>
  <div>
    <!-- Start Recording Modal -->
    <div v-if="state === 'start'" 
         class="fixed z-50"
         :style="{ left: position.x + 'px', top: position.y + 'px' }"
         @mousedown="startDrag">
      <div class="bg-white/95 backdrop-blur-md w-[360px] box-border px-8 py-10 rounded-3xl shadow-2xl border border-white/80 relative text-center select-none animate-[fadeIn_0.3s_ease-out] cursor-move">
        <button class="absolute top-5 right-5 cursor-pointer text-gray-400 hover:text-gray-800 hover:bg-gray-100/50 rounded-full w-8 h-8 flex items-center justify-center transition-all duration-200 hover:rotate-90" @mousedown.stop @click="$emit('close')">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
        </button>
        
        <div class="w-[88px] h-[88px] mx-auto mb-6 bg-gradient-to-b from-blue-50 to-blue-50/50 rounded-[28px] flex justify-center items-center shadow-[0_8px_16px_-4px_rgba(75,139,245,0.15)] ring-1 ring-inset ring-white/50 relative">
            <svg width="50" height="50" viewBox="0 0 24 24" fill="#4B8BF5" class="drop-shadow-md">
                <path d="M14 2H6C4.9 2 4 2.9 4 4V20C4 21.1 4.9 22 6 22H18C19.1 22 20 21.1 20 20V8L14 2Z" fill="#8FB5FE"/>
                <path d="M14 2V8H20" fill="#669DF6"/>
                <path d="M8 12H16M8 16H16" stroke="white" stroke-width="2" stroke-linecap="round"/>
            </svg>
            <div class="absolute -bottom-1 -right-1 bg-gradient-to-br from-blue-400 to-blue-500 text-white rounded-full w-9 h-9 flex items-center justify-center shadow-lg border-2 border-white">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="white">
                    <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                    <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
                </svg>
            </div>
        </div>
        
        <h2 class="text-xl text-gray-900 mb-3 font-bold tracking-tight">录音纪要</h2>
        <div class="text-sm text-gray-500 mb-8 leading-relaxed">
            实时转文字<br>
            录音结束后查看会议总结
        </div>

        <!-- Settings Controls -->
        <div class="flex gap-3 mb-6 justify-center" @mousedown.stop>
            <a-select v-model:value="format" style="width: 120px" class="text-left">
                <a-select-option value="mp3">MP3 格式</a-select-option>
                <a-select-option value="wav">WAV 格式</a-select-option>
            </a-select>
            <a-select v-model:value="vizType" style="width: 130px" class="text-left">
                <a-select-option value="histogram">频率直方图</a-select-option>
                <a-select-option value="wave">实时波形图</a-select-option>
            </a-select>
        </div>

        <button class="w-full py-3.5 rounded-xl border-none text-base font-semibold cursor-pointer transition-all duration-200 mb-4 bg-gradient-to-br from-blue-500 to-blue-600 text-white shadow-lg hover:-translate-y-px hover:shadow-xl hover:brightness-105 active:translate-y-0 active:shadow-md" @mousedown.stop @click="startRecording">开始录音</button>
      </div>
    </div>

    <!-- Recording State -->
    <div v-if="state === 'recording'" 
         class="fixed z-50"
         :style="{ left: position.x + 'px', top: position.y + 'px' }"
         @mousedown="startDrag">
      <div class="bg-white/95 backdrop-blur-md w-[360px] box-border px-8 py-10 rounded-3xl shadow-2xl border border-white/80 relative text-center select-none animate-[fadeIn_0.3s_ease-out] cursor-move">
         <!-- Header -->
        <div class="flex justify-between items-start mb-8">
            <div class="flex items-center gap-2">
                 <div class="w-2.5 h-2.5 bg-blue-500 rounded-full animate-pulse"></div>
                 <span class="text-blue-500 font-bold text-lg">{{ isPaused ? '已暂停' : '录音转写中...' }}</span>
            </div>
            <div class="flex items-center gap-1" @mousedown.stop>
                <button class="w-8 h-8 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors" @click="stopRecording">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
            </div>
        </div>

        <!-- Visualization -->
        <div class="h-[100px] flex items-center justify-center relative w-full mb-4">
             <div id="wave-canvas" class="w-full h-full opacity-80"></div> 
        </div>

        <!-- Timer -->
        <div class="text-3xl font-bold text-gray-800 mb-8 font-din tabular-nums">{{ timerText }}</div>

        <!-- Controls -->
        <div class="flex justify-center gap-6" @mousedown.stop>
             <button class="w-14 h-14 rounded-2xl flex items-center justify-center transition-all duration-200 bg-amber-50 text-amber-500 hover:bg-amber-100 border border-amber-200" @click="togglePause">
                <svg v-if="!isPaused" width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                    <rect x="6" y="5" width="4" height="14" rx="1"></rect>
                    <rect x="14" y="5" width="4" height="14" rx="1"></rect>
                </svg>
                <svg v-else width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                     <path d="M8 5v14l11-7z"></path>
                </svg>
            </button>
            <button class="w-14 h-14 rounded-2xl flex items-center justify-center transition-all duration-200 bg-red-50 text-red-500 hover:bg-red-100 border border-red-200" @click="stopRecording">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                    <rect x="6" y="6" width="12" height="12" rx="2"></rect>
                </svg>
            </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, reactive } from 'vue';
import { message } from 'ant-design-vue';
import dayjs from 'dayjs';

const emit = defineEmits(['close', 'finish']);

const state = ref('start'); // start, recording
const format = ref('mp3');
const vizType = ref('histogram');
const isPaused = ref(false);
const timerText = ref('00:00');

// Dragging state
const position = reactive({ x: 0, y: 0 });
const dragOffset = reactive({ x: 0, y: 0 });
let isDragging = false;

let rec = null;
let wave = null;
let timerInterval = null;
let startTime = 0;
let totalPauseTime = 0;
let pauseTime = 0;

// Dragging Logic
const startDrag = (e) => {
    isDragging = true;
    dragOffset.x = e.clientX - position.x;
    dragOffset.y = e.clientY - position.y;
    
    document.addEventListener('mousemove', onDrag);
    document.addEventListener('mouseup', stopDrag);
};

const onDrag = (e) => {
    if (!isDragging) return;
    position.x = e.clientX - dragOffset.x;
    position.y = e.clientY - dragOffset.y;
};

const stopDrag = () => {
    isDragging = false;
    document.removeEventListener('mousemove', onDrag);
    document.removeEventListener('mouseup', stopDrag);
};

// Set initial position (Top-Right)
const setInitialPosition = () => {
    const width = 360; // Approximate width from tailwind class
    // 20px margin from top and right
    position.x = window.innerWidth - width - 20;
    position.y = 20;
    
    // Safety check to ensure it's not off-screen on very small screens
    if (position.x < 0) position.x = 0;
};

// Load scripts helper
const loadScript = (src) => {
    return new Promise((resolve, reject) => {
        if (document.querySelector(`script[src="${src}"]`)) {
            resolve();
            return;
        }
        const script = document.createElement('script');
        script.src = src;
        script.onload = resolve;
        script.onerror = reject;
        document.body.appendChild(script);
    });
};

const initRecorder = async () => {
    try {
        await loadScript('/recorder-lib/recorder-core.js');
        await loadScript('/recorder-lib/mp3.js');
        await loadScript('/recorder-lib/mp3-engine.js');
        await loadScript('/recorder-lib/wav.js');
        await loadScript('/recorder-lib/lib.fft.js');
        await loadScript('/recorder-lib/frequency.histogram.view.js');
        await loadScript('/recorder-lib/waveview.js');
    } catch (e) {
        message.error("Failed to load recorder libraries");
        console.error(e);
    }
};

onMounted(() => {
    setInitialPosition();
    initRecorder();
    window.addEventListener('resize', setInitialPosition);
});

onUnmounted(() => {
    if (rec) {
        rec.close();
    }
    clearInterval(timerInterval);
    window.removeEventListener('resize', setInitialPosition);
    stopDrag(); // Cleanup just in case
});

const startRecording = () => {
    if (!window.Recorder) {
        message.error("Recorder library not loaded yet");
        return;
    }

    rec = window.Recorder({
        type: format.value,
        sampleRate: 16000,
        bitRate: 16,
        onProcess: (buffers, powerLevel, bufferDuration, bufferSampleRate) => {
            if (wave) {
                wave.input(buffers[buffers.length - 1], powerLevel, bufferSampleRate);
            }
        }
    });

    rec.open(() => {
        rec.start();
        state.value = 'recording';
        startTimer();
        
        // Init Viz
        setTimeout(() => {
            const elem = document.querySelector('#wave-canvas');
            if(elem) elem.innerHTML = '';
            
            if (vizType.value === 'histogram') {
                wave = window.Recorder.FrequencyHistogramView({
                    elem: "#wave-canvas",
                    lineCount: 30,
                    position: 0,
                    minHeight: 1,
                    fallDuration: 400,
                    stripeEnable: false,
                    mirrorEnable: true
                });
            } else {
                wave = window.Recorder.WaveView({
                    elem: "#wave-canvas"
                });
            }
        }, 100);

    }, (msg, isUserNotAllow) => {
        message.error("Unable to open recorder: " + msg);
    });
};

const stopRecording = () => {
    if (rec) {
        rec.stop((blob, duration) => {
            rec.close();
            rec = null;
            clearInterval(timerInterval);
            
            const now = dayjs().format('YYYY-MM-DD HH:mm:ss');
            const fileName = `新录音 ${dayjs().format('HH:mm:ss')}.${format.value}`;
            
            emit('finish', {
                blob,
                duration,
                fileName,
                createdAt: now,
                format: format.value
            });
            
            state.value = 'start'; // Reset or close
            emit('close');
            
        }, (msg) => {
            message.error("Stop failed: " + msg);
        });
    }
};

const togglePause = () => {
    if (isPaused.value) {
        rec.resume();
        if (pauseTime) {
            totalPauseTime += (Date.now() - pauseTime);
            pauseTime = 0;
        }
        timerInterval = setInterval(updateTimer, 1000);
        isPaused.value = false;
    } else {
        rec.pause();
        clearInterval(timerInterval);
        pauseTime = Date.now();
        isPaused.value = true;
    }
};

const startTimer = () => {
    startTime = Date.now();
    totalPauseTime = 0;
    clearInterval(timerInterval);
    timerInterval = setInterval(updateTimer, 1000);
};

const updateTimer = () => {
    const now = Date.now();
    const duration = now - startTime - totalPauseTime;
    const seconds = Math.floor(duration / 1000);
    const min = Math.floor(seconds / 60);
    const sec = seconds % 60;
    timerText.value = (min < 10 ? "0" + min : min) + ":" + (sec < 10 ? "0" + sec : sec);
};

onUnmounted(() => {
    if (rec) {
        rec.close();
    }
    clearInterval(timerInterval);
});

</script>