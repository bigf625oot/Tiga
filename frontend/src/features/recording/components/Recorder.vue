<template>
  <div>
    <!-- Start Recording Modal -->
    <div v-if="state === 'start'" 
         class="fixed z-50"
         :style="{ left: position.x + 'px', top: position.y + 'px' }"
         @mousedown="startDrag">
      <div class="bg-background/95 backdrop-blur-md supports-[backdrop-filter]:bg-background/60 w-[360px] px-8 py-10 rounded-xl shadow-2xl border border-border relative text-center select-none animate-in fade-in zoom-in duration-300 cursor-move ring-1 ring-border/50">
        <TooltipProvider>
            <Tooltip>
                <TooltipTrigger as-child>
                    <Button variant="ghost" size="icon" class="absolute top-4 right-4 h-8 w-8 rounded-full hover:bg-muted" @mousedown.stop @click="$emit('close')">
                        <X class="h-4 w-4" />
                    </Button>
                </TooltipTrigger>
                <TooltipContent>关闭</TooltipContent>
            </Tooltip>
        </TooltipProvider>
        
        <div class="w-20 h-20 mx-auto mb-6 bg-primary/10 rounded-3xl flex justify-center items-center shadow-inner ring-1 ring-inset ring-background/50 relative">
            <Mic class="w-10 h-10 text-primary drop-shadow-sm" />
            <div class="absolute -bottom-2 -right-2 bg-gradient-to-br from-primary to-primary/80 text-primary-foreground rounded-full w-8 h-8 flex items-center justify-center shadow-lg border-2 border-background">
                <Plus class="w-5 h-5" />
            </div>
        </div>
        
        <h2 class="text-xl text-foreground m-4 font-semibold tracking-tight">录音纪要</h2>
        <div class="text-sm text-muted-foreground mb-8 leading-relaxed">
            实时转文字<br>
            录音结束后查看会议总结
        </div>

        <!-- Settings Controls -->
        <div class="flex gap-4 mb-6 justify-center" @mousedown.stop>
            <Select v-model="format">
                <SelectTrigger class="w-[120px]">
                    <SelectValue placeholder="格式" />
                </SelectTrigger>
                <SelectContent>
                    <SelectItem value="mp3">MP3 格式</SelectItem>
                    <SelectItem value="wav">WAV 格式</SelectItem>
                </SelectContent>
            </Select>

            <Select v-model="vizType">
                <SelectTrigger class="w-[130px]">
                    <SelectValue placeholder="视图" />
                </SelectTrigger>
                <SelectContent>
                    <SelectItem value="histogram">频率直方图</SelectItem>
                    <SelectItem value="wave">实时波形图</SelectItem>
                </SelectContent>
            </Select>
        </div>

        <Button size="lg" class="w-full font-semibold shadow-lg shadow-primary/20 hover:-translate-y-0.5 transition-all" @mousedown.stop @click="startRecording">开始录音</Button>
      </div>
    </div>

    <!-- Recording State -->
    <div v-if="state === 'recording'" 
         class="fixed z-50"
         :style="{ left: position.x + 'px', top: position.y + 'px' }"
         @mousedown="startDrag">
      <div class="bg-background/95 backdrop-blur-md supports-[backdrop-filter]:bg-background/60 w-[360px] px-8 py-10 rounded-xl shadow-2xl border border-border relative text-center select-none animate-in fade-in zoom-in duration-300 cursor-move ring-1 ring-border/50">
         <!-- Header -->
        <div class="flex justify-between items-start mb-8">
            <div class="flex items-center gap-2">
                 <div class="w-2.5 h-2.5 bg-primary rounded-full animate-pulse"></div>
                 <span class="text-primary font-semibold text-lg">{{ isPaused ? '已暂停' : '录音转写中...' }}</span>
            </div>
            <div class="flex items-center gap-1" @mousedown.stop>
                <TooltipProvider>
                    <Tooltip>
                        <TooltipTrigger as-child>
                            <Button variant="ghost" size="icon" class="h-8 w-8 rounded-lg text-muted-foreground hover:text-foreground" @click="stopRecording">
                                <X class="h-4 w-4" />
                            </Button>
                        </TooltipTrigger>
                        <TooltipContent>结束录音</TooltipContent>
                    </Tooltip>
                </TooltipProvider>
            </div>
        </div>

        <!-- Visualization -->
        <div class="h-[100px] flex items-center justify-center relative w-full mb-4 bg-muted/20 rounded-lg overflow-hidden border border-border/50">
             <div id="wave-canvas" class="w-full h-full opacity-80"></div> 
        </div>

        <!-- Timer -->
        <div class="text-4xl font-bold text-foreground mb-8 font-mono tabular-nums tracking-wider">{{ timerText }}</div>

        <!-- Controls -->
        <div class="flex justify-center gap-6" @mousedown.stop>
             <TooltipProvider>
                <Tooltip>
                    <TooltipTrigger as-child>
                        <Button 
                            variant="outline" 
                            size="icon" 
                            class="w-14 h-14 rounded-2xl border-2 transition-all duration-200"
                            :class="isPaused ? 'bg-primary text-primary-foreground hover:bg-primary/90 border-transparent shadow-lg shadow-primary/20' : 'bg-amber-50 text-amber-600 hover:bg-amber-100 border-amber-200 dark:bg-amber-950/30 dark:border-amber-900/50'"
                            @click="togglePause"
                        >
                            <Play v-if="isPaused" class="w-6 h-6 ml-1 fill-current" />
                            <Pause v-else class="w-6 h-6 fill-current" />
                        </Button>
                    </TooltipTrigger>
                    <TooltipContent>{{ isPaused ? '继续' : '暂停' }}</TooltipContent>
                </Tooltip>
            </TooltipProvider>
            
            <TooltipProvider>
                <Tooltip>
                    <TooltipTrigger as-child>
                        <Button 
                            variant="outline" 
                            size="icon" 
                            class="w-14 h-14 rounded-2xl border-2 transition-all duration-200 bg-red-50 text-red-600 hover:bg-red-100 border-red-200 dark:bg-red-950/30 dark:border-red-900/50"
                            @click="stopRecording"
                        >
                            <Square class="w-6 h-6 fill-current" />
                        </Button>
                    </TooltipTrigger>
                    <TooltipContent>停止并保存</TooltipContent>
                </Tooltip>
            </TooltipProvider>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, reactive } from 'vue';
import { useToast } from '@/components/ui/toast/use-toast';
import dayjs from 'dayjs';
import { X, Mic, Plus, Play, Pause, Square } from 'lucide-vue-next';

// Shadcn Components
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

const emit = defineEmits(['close', 'finish']);

const { toast } = useToast();

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
        toast({ variant: "destructive", title: "无法加载录音库", description: "请检查网络连接" });
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
        toast({ variant: "destructive", title: "录音组件未就绪", description: "请稍候再试" });
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
        toast({ variant: "destructive", title: "无法打开录音", description: isUserNotAllow ? "请允许浏览器访问麦克风" : msg });
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
            toast({ variant: "destructive", title: "停止失败", description: msg });
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
</script>
