import { InjectionKey, Ref, ref, provide, inject } from 'vue';

export interface Artifact {
  id: string;
  type: 'code' | 'markdown' | 'vue' | 'html' | 'json';
  content: string;
  title?: string;
  language?: string;
}

export interface ArtifactContext {
  activeArtifact: Ref<Artifact | null>;
  isArtifactOpen: Ref<boolean>;
  openArtifact: (artifact: Omit<Artifact, 'id'> & { id?: string }) => void;
  closeArtifact: () => void;
}

export const ArtifactContextKey: InjectionKey<ArtifactContext> = Symbol('ArtifactContext');

export function useArtifactProvider() {
  const activeArtifact = ref<Artifact | null>(null);
  const isArtifactOpen = ref(false);

  const openArtifact = (artifact: Omit<Artifact, 'id'> & { id?: string }) => {
    activeArtifact.value = {
      id: artifact.id || Math.random().toString(36).substring(2, 9),
      ...artifact
    };
    isArtifactOpen.value = true;
  };

  const closeArtifact = () => {
    isArtifactOpen.value = false;
    // Don't clear activeArtifact immediately to allow close animation to finish smoothly
    setTimeout(() => {
      if (!isArtifactOpen.value) {
        activeArtifact.value = null;
      }
    }, 300);
  };

  const context: ArtifactContext = {
    activeArtifact,
    isArtifactOpen,
    openArtifact,
    closeArtifact
  };

  provide(ArtifactContextKey, context);

  return context;
}

export function useArtifact() {
  const context = inject(ArtifactContextKey);
  if (!context) {
    throw new Error('useArtifact must be used within a component that calls useArtifactProvider');
  }
  return context;
}
