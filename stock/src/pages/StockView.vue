<script setup>
import { ref, watch, computed } from 'vue';
import { useRoute } from 'vue-router';
import { joinURL } from 'ufo';

import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import ProgressSpinner from 'primevue/progressspinner';
import Breadcrumb from 'primevue/breadcrumb';
import SelectButton from 'primevue/selectbutton';
import ToggleButton from 'primevue/togglebutton';
import Chart from 'primevue/chart';
import ChartDataLabels from 'chartjs-plugin-datalabels';

const route = useRoute();
const tickerInfo = ref(null);
const dividendHistory = ref([]);
const isLoading = ref(true);
const error = ref(null);

const timeRangeOptions = ref([]);
const selectedTimeRange = ref('1Y');
const isPriceChartMode = ref(false);

const chartData = ref();
const chartOptions = ref();

const fetchData = async (tickerName) => {
  isLoading.value = true;
  error.value = null;
  tickerInfo.value = null;
  dividendHistory.value = [];
  timeRangeOptions.value = [];

  const url = joinURL(import.meta.env.BASE_URL, `data/${tickerName.toLowerCase()}.json`);

  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`File not found`);
    const responseData = await response.json();

    tickerInfo.value = responseData.tickerInfo;
    
    const sortedHistory = responseData.dividendHistory.sort((a, b) => 
        new Date(b['배당락일']) - new Date(a['배당락일'])
    );
    dividendHistory.value = sortedHistory;
    
    generateDynamicTimeRangeOptions();

  } catch (err) {
    error.value = `${tickerInfo.value?.티커 || tickerName.toUpperCase()}의 분배금 정보를 찾을 수 없습니다.`;
  } finally {
    isLoading.value = false;
  }
};

const generateDynamicTimeRangeOptions = () => {
    if (dividendHistory.value.length === 0) {
        timeRangeOptions.value = [];
        return;
    }
    const oldestRecordDate = new Date(dividendHistory.value[dividendHistory.value.length - 1]['배당락일']);
    const now = new Date();
    const options = [];
    const oneYearAgo = new Date(new Date().setFullYear(now.getFullYear() - 1));
    const twoYearsAgo = new Date(new Date().setFullYear(now.getFullYear() - 2));
    const threeYearsAgo = new Date(new Date().setFullYear(now.getFullYear() - 3));

    if (oldestRecordDate < oneYearAgo) options.push('1Y');
    if (oldestRecordDate < twoYearsAgo) options.push('2Y');
    if (oldestRecordDate < threeYearsAgo) options.push('3Y');
    
    options.push('Max');
    timeRangeOptions.value = options;

    if (!options.includes(selectedTimeRange.value)) {
        selectedTimeRange.value = options[0] || 'Max';
    }
};

const columns = computed(() => {
  if (dividendHistory.value.length === 0) return [];
  return Object.keys(dividendHistory.value[0]).map(key => ({ field: key, header: key }));
});

const chartDisplayData = computed(() => {
  if (dividendHistory.value.length === 0) return [];
  
  if (selectedTimeRange.value === 'Max') {
    return [...dividendHistory.value].reverse();
  }

  const now = new Date();
  const years = parseInt(selectedTimeRange.value.replace('Y', ''), 10);
  const cutoffDate = new Date(new Date().setFullYear(now.getFullYear() - years));

  const filteredData = dividendHistory.value.filter(item => new Date(item['배당락일']) >= cutoffDate);
  
  return filteredData.reverse();
});

const setChartDataAndOptions = (data, frequency) => {
    const documentStyle = getComputedStyle(document.documentElement);
    const textColor = documentStyle.getPropertyValue('--p-text-color');
    const textColorSecondary = documentStyle.getPropertyValue('--p-text-muted-color');
    const surfaceBorder = documentStyle.getPropertyValue('--p-content-border-color');

    if (frequency === 'Weekly' && !isPriceChartMode.value) {
        const monthlyAggregated = data.reduce((acc, item) => {
            const date = new Date(item['배당락일']);
            const yearMonth = `${date.getFullYear().toString().slice(-2)}.${(date.getMonth() + 1).toString().padStart(2, '0')}`;
            const amount = parseFloat(item['배당금']?.replace('$', '') || 0);
            const weekOfMonth = Math.floor((date.getDate() - 1) / 7) + 1;

            if (!acc[yearMonth]) {
                acc[yearMonth] = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, total: 0 };
            }
            acc[yearMonth][weekOfMonth] += amount;
            acc[yearMonth].total += amount;
            return acc;
        }, {});

        const labels = Object.keys(monthlyAggregated);
        const weekColors = {
            1: 'rgba(54, 162, 235, 0.8)', 2: 'rgba(255, 99, 132, 0.8)',
            3: 'rgba(255, 206, 86, 0.8)', 4: 'rgba(75, 192, 192, 0.8)',
            5: 'rgba(255, 159, 64, 0.8)',
        };
        
        const datasets = [1, 2, 3, 4, 5].map(week => ({
            type: 'bar',
            label: `${week}주차`,
            backgroundColor: weekColors[week],
            data: labels.map(label => monthlyAggregated[label][week] || 0),
            datalabels: {
                display: (context) => context.dataset.data[context.dataIndex] > 0.0001,
                formatter: (value) => `$${value.toFixed(4)}`,
                color: '#fff',
                font: { size: 15, weight: 'bold' },
                align: 'center',
                anchor: 'center'
            }
        }));
        
        // --- 월별 총합을 표시하기 위한 '가상' 데이터셋 수정 ---
        datasets.push({
            type: 'bar',
            label: 'Total',
            // --- 핵심 수정: 데이터 값을 모두 0으로 설정 ---
            // 이렇게 하면 스택의 높이에 영향을 주지 않습니다.
            data: new Array(labels.length).fill(0), 
            backgroundColor: 'transparent',
            datalabels: {
                display: true,
                // formatter는 데이터 값(이제 0) 대신, context를 이용해 총합을 계산하여 표시
                formatter: (value, context) => {
                    const monthLabel = context.chart.data.labels[context.dataIndex];
                    const total = monthlyAggregated[monthLabel]?.total || 0;
                    return total > 0 ? `$${total.toFixed(4)}` : '';
                },
                color: textColor,
                anchor: 'end',
                align: 'end',
                offset: 10, // 막대 상단에서 약간 위로 띄움
                font: { size: 15, weight: 'bold' }
            }
        });

        chartData.value = { labels, datasets };
        chartOptions.value = {
            maintainAspectRatio: false,
            aspectRatio: 0.8,
            plugins: {
                title: { display: true, text: '월별 주차 배당금 누적' },
                tooltip: {
                    mode: 'index',
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (context.parsed.y !== null && context.parsed.y > 0) {
                                label += `: $${context.parsed.y.toFixed(4)}`;
                            } else {
                                return null;
                            }
                            return label;
                        },
                        footer: (tooltipItems) => {
                            let sum = tooltipItems.reduce((a, b) => a + b.parsed.y, 0);
                            return 'Total: $' + sum.toFixed(4);
                        },
                    },
                },
                legend: {
                    labels: {
                        color: textColor,
                        filter: (legendItem) => legendItem.datasetIndex < 5
                    }
                },
                datalabels: { display: true }
            },
            scales: {
                x: { stacked: true, ticks: { color: textColorSecondary }, grid: { color: surfaceBorder } },
                y: { stacked: true, ticks: { color: textColorSecondary }, grid: { color: surfaceBorder } }
            }
        };

    } else {
        const prices = data.flatMap(item => [
            parseFloat(item['배당락전일종가']?.replace('$', '')),
            parseFloat(item['배당락일종가']?.replace('$', ''))
        ]).filter(p => !isNaN(p));
        
        const priceMin = prices.length > 0 ? Math.min(...prices) * 0.98 : 0;
        const priceMax = prices.length > 0 ? Math.max(...prices) * 1.02 : 1;

        chartData.value = {
            labels: data.map(item => item['배당락일']),
            datasets: [
                {
                    type: 'bar', label: '배당금', yAxisID: 'y', order: 2,
                    backgroundColor: documentStyle.getPropertyValue('--p-cyan-400'),
                    data: data.map(item => parseFloat(item['배당금']?.replace('$', '') || 0)),
                    datalabels: {
                        anchor: 'end', align: 'end', color: textColor,
                        formatter: (value) => value > 0 ? `$${value.toFixed(2)}` : null
                    }
                },
                {
                    type: 'line', label: '배당락전일종가', yAxisID: 'y1', order: 1,
                    borderColor: documentStyle.getPropertyValue('--p-orange-500'),
                    data: data.map(item => parseFloat(item['배당락전일종가']?.replace('$', ''))),
                    tension: 0.4, borderWidth: 2, fill: false,
                },
                {
                    type: 'line', label: '배당락일종가', yAxisID: 'y1', order: 1,
                    borderColor: documentStyle.getPropertyValue('--p-gray-500'),
                    data: data.map(item => parseFloat(item['배당락일종가']?.replace('$', ''))),
                    tension: 0.4, borderWidth: 2, fill: false,
                }
            ]
        };
        chartOptions.value = {
            maintainAspectRatio: false,
            aspectRatio: 0.6,
            plugins: {
                legend: { labels: { color: textColor } },
                datalabels: { display: context => context.dataset.type === 'bar' }
            },
            scales: {
                x: { ticks: { color: textColorSecondary }, grid: { color: surfaceBorder } },
                y: { type: 'linear', display: true, position: 'left', ticks: { color: textColorSecondary }, grid: { color: surfaceBorder } },
                y1: {
                    type: 'linear', display: true, position: 'right', min: priceMin, max: priceMax,
                    ticks: { color: textColorSecondary },
                    grid: { drawOnChartArea: false, color: surfaceBorder }
                }
            }
        };
    }
};

watch(() => route.params.ticker, (newTicker) => {
  if (newTicker) {
    isPriceChartMode.value = false;
    selectedTimeRange.value = '1Y';
    fetchData(newTicker);
  }
}, { immediate: true });

watch(chartDisplayData, (newData) => {
  if (newData && newData.length > 0 && tickerInfo.value) {
    setChartDataAndOptions(newData, tickerInfo.value.지급주기);
  } else {
    chartData.value = null;
    chartOptions.value = null;
  }
}, { deep: true, immediate: true });

watch(isPriceChartMode, () => {
    if (chartDisplayData.value && chartDisplayData.value.length > 0 && tickerInfo.value) {
        setChartDataAndOptions(chartDisplayData.value, tickerInfo.value.지급주기);
    }
});

const home = ref({ icon: 'pi pi-home', route: '/' });
const breadcrumbItems = computed(() => [
    // { label: 'ETF 목록', route: '/' },  
    { label: tickerInfo.value ? `${tickerInfo.value.운용사}` : 'Loading...' },
    { label: tickerInfo.value ? `${tickerInfo.value.티커}` : 'Loading...' }
]);
</script>
<template>
    <div class="card">
        <Breadcrumb :home="home" :model="breadcrumbItems">
            <template #item="{ item, props }">
                <router-link v-if="item.route" v-slot="{ href, navigate }" :to="item.route" custom>
                    <a :href="href" v-bind="props.action" @click="navigate">
                        <span :class="[item.icon, 'text-color']" />
                        <span class="text-primary font-semibold">{{ item.label }}</span>
                    </a>
                </router-link>
                <a v-else :href="item.url" :target="item.target" v-bind="props.action">
                    <span class="text-surface-700 dark:text-surface-0">{{ item.label }}</span>
                </a>
            </template>
        </Breadcrumb>

        <!-- 로딩 중일 때는 제목을 표시하지 않음 -->
        <div v-if="!isLoading && tickerInfo">
            <h2 class="mt-4">{{ tickerInfo.티커 }} 분배금 정보</h2>
            <p>운용사: {{ tickerInfo.운용사 }} | 지급주기: {{ tickerInfo.지급주기 }}</p>
        </div>

        <div v-if="isLoading" class="flex justify-center items-center h-48">
            <ProgressSpinner />
        </div>

        <div v-else-if="error">
            <p class="text-red-500">{{ error }}</p>
        </div>

        <template v-else-if="dividendHistory.length > 0">
            <!-- 1. 데이터 개수 선택 UI 수정 -->
            <!-- UI 컨트롤 영역 -->
            <div class="my-4 flex justify-between items-center">
                <!-- 토글 버튼 (Weekly ETF일 때만 보임) -->
                <div v-if="tickerInfo?.지급주기 === 'Weekly'">
                    <ToggleButton v-model="isPriceChartMode" onLabel="주가 차트" offLabel="배당금 차트" onIcon="pi pi-chart-line"
                        offIcon="pi pi-chart-bar" />
                </div>
                <!-- 빈 공간을 채우기 위한 div (토글 버튼이 없을 때도 레이아웃 유지) -->
                <div v-else></div>

                <!-- 시간 범위 선택 버튼 -->
                <SelectButton v-model="selectedTimeRange" :options="timeRangeOptions" aria-labelledby="basic" />
            </div>
            <div class="card" id="p-chart">
                <Chart type="bar" :data="chartData" :options="chartOptions" :plugins="[ChartDataLabels]" />
            </div>
            <DataTable :value="dividendHistory" responsiveLayout="scroll" stripedRows scrollable scrollHeight="50vh">
                <Column v-for="col in columns" :key="col.field" :field="col.field" :header="col.header"></Column>
            </DataTable>
        </template>

        <div v-else>
            <p>표시할 데이터가 없습니다.</p>
        </div>
    </div>
</template>