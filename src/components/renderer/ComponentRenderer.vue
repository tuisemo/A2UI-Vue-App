<script setup lang="ts">
import { computed } from "vue";
import { useA2UIStore } from "@/stores/a2ui";
import A2Chart from "@/components/ui/A2Chart.vue";
import A2Markdown from "@/components/ui/A2Markdown.vue";
import A2Table from "@/components/ui/A2Table.vue";
import A2Progress from "@/components/ui/A2Progress.vue";
import A2Badge from "@/components/ui/A2Badge.vue";
import A2Avatar from "@/components/ui/A2Avatar.vue";
import A2Alert from "@/components/ui/A2Alert.vue";
import A2Rating from "@/components/ui/A2Rating.vue";
import A2Stat from "@/components/ui/A2Stat.vue";
import A2Steps from "@/components/ui/A2Steps.vue";
import A2Accordion from "@/components/ui/A2Accordion.vue";
import A2Timeline from "@/components/ui/A2Timeline.vue";
import A2Price from "@/components/ui/A2Price.vue";
import A2TagList from "@/components/ui/A2TagList.vue";
import A2MetricCard from "@/components/ui/A2MetricCard.vue";
import A2Figure from "@/components/ui/A2Figure.vue";
import A2Quote from "@/components/ui/A2Quote.vue";

const props = defineProps<{ id: string; msgId: string }>();
const emit = defineEmits<{ (e: "action", action: any): void }>();

const store = useA2UIStore();

const component = computed(() => store.getComponent(props.msgId, props.id));
const type = computed(() => component.value?.type || null);
const p = computed(() => component.value?.props || {});
const children = computed(() => component.value?.children || []);

// Resolve value from literalString or path binding (supports any type)
function resolveValue(val: any, defaultVal: any = ''): any {
  if (val === null || val === undefined) return defaultVal;
  if (typeof val === 'string' || typeof val === 'number' || typeof val === 'boolean') return val;
  if (val.literalString !== undefined) return val.literalString;
  if (val.literalNumber !== undefined) return val.literalNumber;
  if (val.literalBoolean !== undefined) return val.literalBoolean;
  if (val.path) return store.getDataAtPath(props.msgId, val.path) ?? defaultVal;
  return defaultVal;
}

const layoutClasses = computed(() => {
    const classes = [
        type.value === "Column" ? "flex-col" : "flex-row",
        "flex gap-4 w-full",
    ];
    if (p.value.alignment === "center") classes.push("items-center");
    if (p.value.alignment === "start") classes.push("items-start");
    if (p.value.alignment === "end") classes.push("items-end");
    if (p.value.alignment === "stretch") classes.push("items-stretch");
    if (p.value.distribution === "center") classes.push("justify-center");
    if (p.value.distribution === "spaceBetween")
        classes.push("justify-between");
    if (p.value.distribution === "spaceAround") classes.push("justify-around");
    return classes.join(" ");
});

const textClasses = computed(() => {
    const hint = p.value.usageHint;
    const base = "font-sans";
    if (hint === "h1")
        return `${base} text-3xl font-extrabold tracking-tight text-slate-900`;
    if (hint === "h2") return `${base} text-2xl font-bold text-slate-900`;
    if (hint === "h3") return `${base} text-xl font-semibold text-slate-800`;
    if (hint === "h4") return `${base} text-lg font-semibold text-slate-800`;
    if (hint === "h5")
        return `${base} text-sm font-semibold uppercase tracking-wide text-slate-500`;
    if (hint === "caption") return `${base} text-sm text-slate-500`;
    return `${base} text-base text-slate-600 leading-relaxed`;
});

const handleAction = () => {
    if (p.value.action)
        emit("action", { ...p.value.action, sourceId: props.id });
};
</script>

<template>
    <Transition name="fade" mode="out-in" appear>
        <div :key="id" class="w-full">
            <div v-if="!component" class="hidden"></div>

            <!-- Text -->
            <p v-else-if="type === 'Text'" :class="textClasses">
                {{ resolveValue(p.text) }}
            </p>

            <!-- Icon -->
            <span
                v-else-if="type === 'Icon'"
                class="material-symbols-outlined text-2xl text-slate-500"
            >
                {{ resolveValue(p.name) }}
            </span>

            <!-- Button -->
            <button
                v-else-if="type === 'Button'"
                :class="p.primary ? 'btn-primary' : 'btn-secondary'"
                @click="handleAction"
            >
                <ComponentRenderer
                    v-for="cid in children"
                    :key="cid"
                    :id="cid"
                    :msg-id="msgId"
                    @action="$emit('action', $event)"
                />
            </button>

            <!-- Card -->
            <div
                v-else-if="type === 'Card'"
                class="glass-panel hover:-translate-y-1"
            >
                <ComponentRenderer
                    v-for="cid in children"
                    :key="cid"
                    :id="cid"
                    :msg-id="msgId"
                    @action="$emit('action', $event)"
                />
            </div>

            <!-- Column / Row -->
            <div
                v-else-if="type === 'Column' || type === 'Row'"
                :class="layoutClasses"
            >
                <ComponentRenderer
                    v-for="cid in children"
                    :key="cid"
                    :id="cid"
                    :msg-id="msgId"
                    @action="$emit('action', $event)"
                />
            </div>

            <!-- List -->
            <div v-else-if="type === 'List'" class="flex flex-col gap-3 w-full">
                <ComponentRenderer
                    v-for="cid in children"
                    :key="cid"
                    :id="cid"
                    :msg-id="msgId"
                    @action="$emit('action', $event)"
                />
            </div>

            <!-- Image -->
            <img
                v-else-if="type === 'Image'"
                :src="resolveValue(p.url)"
                class="w-full rounded-xl object-cover aspect-video"
                loading="lazy"
            />

            <!-- Divider -->
            <hr
                v-else-if="type === 'Divider'"
                class="w-full border-t border-slate-200 my-4"
            />

            <!-- TextField -->
            <div v-else-if="type === 'TextField'" class="w-full">
                <label
                    v-if="p.label"
                    class="block text-sm font-medium text-slate-700 mb-1.5"
                >
                    {{ resolveValue(p.label) }}
                </label>
                <input
                    type="text"
                    class="input-field"
                    :placeholder="resolveValue(p.placeholder)"
                />
            </div>

            <!-- CheckBox -->
            <label
                v-else-if="type === 'CheckBox'"
                class="flex items-center gap-3 cursor-pointer"
            >
                <input
                    type="checkbox"
                    class="w-5 h-5 accent-slate-900 rounded"
                />
                <span class="text-slate-700">{{ resolveValue(p.label) }}</span>
            </label>

            <!-- Slider -->
            <div v-else-if="type === 'Slider'" class="w-full">
                <div class="flex justify-between text-sm text-slate-600 mb-2">
                    <span>{{ resolveValue(p.label) }}</span>
                    <span class="font-medium">{{ p.value || 50 }}</span>
                </div>
                <input
                    type="range"
                    class="w-full accent-slate-900"
                    :min="p.min || 0"
                    :max="p.max || 100"
                    :value="p.value || 50"
                />
            </div>

            <!-- Tabs -->
            <div v-else-if="type === 'Tabs'" class="w-full">
                <div class="flex gap-1 border-b border-slate-200 mb-4">
                    <button
                        v-for="(tab, i) in p.tabs || []"
                        :key="i"
                        :class="[
                            'px-4 py-2 text-sm font-medium transition-colors',
                            i === 0
                                ? 'text-slate-900 border-b-2 border-slate-900'
                                : 'text-slate-500 hover:text-slate-700',
                        ]"
                    >
                        {{ resolveValue(tab.label) }}
                    </button>
                </div>
                <ComponentRenderer
                    v-if="p.tabs?.[0]?.child"
                    :id="p.tabs[0].child"
                    :msg-id="msgId"
                    @action="$emit('action', $event)"
                />
            </div>

            <!-- Video -->
            <video
                v-else-if="type === 'Video'"
                controls
                class="w-full rounded-xl"
                :autoplay="p.autoplay"
            >
                <source :src="resolveValue(p.url)" type="video/mp4" />
            </video>

            <!-- Audio -->
            <audio
                v-else-if="type === 'Audio' || type === 'AudioPlayer'"
                controls
                class="w-full"
            >
                <source :src="resolveValue(p.url)" type="audio/mpeg" />
            </audio>

            <!-- Chart -->
            <A2Chart
                v-else-if="type === 'Chart'"
                :options="p.options"
                :height="p.height"
            />

            <!-- Markdown -->
            <A2Markdown
                v-else-if="type === 'Markdown'"
                :content="resolveValue(p.content)"
            />

            <!-- Table -->
            <A2Table
                v-else-if="type === 'Table'"
                :columns="p.columns"
                :data="p.data"
                :striped="p.striped"
            />

            <!-- Progress -->
            <A2Progress
                v-else-if="type === 'Progress'"
                :value="resolveValue(p.value, 0)"
                :max="resolveValue(p.max, 100)"
                :show-label="resolveValue(p.showLabel, false)"
                :color="resolveValue(p.color, 'primary')"
            />

            <!-- Badge -->
            <A2Badge
                v-else-if="type === 'Badge'"
                :text="resolveValue(p.text)"
                :variant="resolveValue(p.variant, 'info')"
            />

            <!-- Avatar -->
            <A2Avatar
                v-else-if="type === 'Avatar'"
                :src="resolveValue(p.src)"
                :name="resolveValue(p.name)"
                :size="resolveValue(p.size, 'md')"
            />

            <!-- Alert -->
            <A2Alert
                v-else-if="type === 'Alert'"
                :title="resolveValue(p.title)"
                :message="resolveValue(p.message)"
                :variant="resolveValue(p.variant, 'info')"
            />

            <!-- Rating (NEW) -->
            <A2Rating
                v-else-if="type === 'Rating'"
                :rating="p.rating"
                :max="p.max"
                :size="p.size"
                :show-value="p.showValue"
            />

            <!-- Stat (NEW) -->
            <A2Stat
                v-else-if="type === 'Stat'"
                :label="resolveValue(p.label)"
                :value="resolveValue(p.value)"
                :icon="resolveValue(p.icon)"
                :trend="resolveValue(p.trend)"
                :trend-value="resolveValue(p.trendValue)"
            />

            <!-- Steps (NEW) -->
            <A2Steps
                v-else-if="type === 'Steps'"
                :steps="p.steps"
                :direction="p.direction"
            />

            <!-- Accordion (NEW) -->
            <A2Accordion
                v-else-if="type === 'Accordion'"
                :items="p.items"
                :default-open="p.defaultOpen"
            />

            <!-- Timeline (NEW) -->
            <A2Timeline v-else-if="type === 'Timeline'" :items="p.items" />

            <!-- Price (NEW) -->
            <A2Price
                v-else-if="type === 'Price'"
                :price="p.price"
                :currency="p.currency"
                :period="p.period"
                :original-price="p.originalPrice"
            />

            <!-- TagList (NEW) -->
            <A2TagList v-else-if="type === 'TagList'" :tags="p.tags" />

            <!-- MetricCard (NEW) -->
            <A2MetricCard
                v-else-if="type === 'MetricCard'"
                :title="resolveValue(p.title)"
                :value="resolveValue(p.value)"
                :subtitle="resolveValue(p.subtitle)"
                :icon="resolveValue(p.icon)"
                :color="resolveValue(p.color, 'primary')"
            />

            <!-- Figure (NEW) -->
            <A2Figure
                v-else-if="type === 'Figure'"
                :src="resolveValue(p.src)"
                :alt="p.alt"
                :caption="resolveValue(p.caption)"
                :aspect-ratio="p.aspectRatio"
            />

            <!-- Quote (NEW) -->
            <A2Quote
                v-else-if="type === 'Quote'"
                :content="resolveValue(p.content)"
                :author="resolveValue(p.author)"
                :avatar="resolveValue(p.avatar)"
            />

            <!-- Conditional - render child based on condition -->
            <template v-else-if="type === 'Conditional'">
                <ComponentRenderer
                    v-if="resolveValue(p.condition, false)"
                    :id="p.thenChild"
                    :msg-id="msgId"
                    @action="$emit('action', $event)"
                />
                <ComponentRenderer
                    v-else-if="p.elseChild"
                    :id="p.elseChild"
                    :msg-id="msgId"
                    @action="$emit('action', $event)"
                />
            </template>

            <!-- Fallback -->
            <div
                v-else
                class="px-3 py-2 bg-amber-50 border border-amber-200 rounded-lg text-amber-700 text-sm"
            >
                Unknown component: {{ type }}
            </div>
        </div>
    </Transition>
</template>

<style scoped>
.fade-enter-active {
    transition: opacity 0.25s ease-out, transform 0.25s ease-out;
}
.fade-leave-active {
    transition: opacity 0.15s ease-in, transform 0.15s ease-in;
}
.fade-enter-from {
    opacity: 0;
    transform: translateY(8px);
}
.fade-leave-to {
    opacity: 0;
    transform: translateY(-4px);
}
.fade-move {
    transition: transform 0.3s ease;
}
</style>
