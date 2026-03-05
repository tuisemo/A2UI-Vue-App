<script setup lang="ts">
defineProps<{
  src: string
  alt?: string
  caption?: string
  aspectRatio?: 'video' | 'square' | 'portrait' | 'auto'
}>()

const aspectClasses = {
  video: 'aspect-video',
  square: 'aspect-square',
  portrait: 'aspect-[3/4]',
  auto: ''
}
</script>

<template>
  <figure class="w-full">
    <div class="overflow-hidden rounded-xl bg-slate-100">
      <img 
        :src="src" 
        :alt="alt || ''" 
        :class="['w-full object-cover', aspectClasses[aspectRatio || 'video']]"
        loading="lazy"
        @error="($event.target as HTMLImageElement).src = 'https://placehold.co/600x400?text=Image+Not+Found'"
      />
    </div>
    <figcaption v-if="caption" class="mt-2 text-sm text-slate-500 text-center">{{ caption }}</figcaption>
  </figure>
</template>
