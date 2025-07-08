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
import Panel from 'primevue/panel';
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

const parseYYMMDD = (dateStr) => {
    if (!dateStr || typeof dateStr !== 'string') return null;
    const parts = dateStr.split('.').map(part => part.trim());
    if (parts.length !== 3) return null;
    return new Date(`20${parts[0]}`, parseInt(parts[1], 10) - 1, parts[2]);
};

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
        parseYYMMDD(b['배당락일']) - parseYYMMDD(a['배당락일'])
    );
    dividendHistory.value = sortedHistory;
    
    generateDynamicTimeRangeOptions();
  } catch (err) {
    error.value = `${tickerName.toUpperCase()}의 분배금 정보를 찾을 수 없습니다.`;
  } finally {
    isLoading.value = false;
  }
};

const generateDynamicTimeRangeOptions = () => {
    if (dividendHistory.value.length === 0) return;
    const oldestRecordDate = parseYYMMDD(dividendHistory.value[dividendHistory.value.length - 1]['배당락일']);
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
  if (selectedTimeRange.value === 'Max') return [...dividendHistory.value].reverse();
  const now = new Date();
  const years = parseInt(selectedTimeRange.value.replace('Y', ''), 10);
  const cutoffDate = new Date(new Date().setFullYear(now.getFullYear() - years));
  const filteredData = dividendHistory.value.filter(item => parseYYMMDD(item['배당락일']) >= cutoffDate);
  return filteredData.reverse();
});

const setChartDataAndOptions = (data, frequency) => {
    const documentStyle = getComputedStyle(document.documentElement);
    const textColor = documentStyle.getPropertyValue('--p-text-color');
    const textColorSecondary = documentStyle.getPropertyValue('--p-text-muted-color');
    const surfaceBorder = documentStyle.getPropertyValue('--p-content-border-color');

    // --- Weekly ETF의 배당금 차트 모드 (핵심 수정) ---
    if (frequency === 'Weekly' && !isPriceChartMode.value) {
        const monthlyAggregated = data.reduce((acc, item) => {
            const date = parseYYMMDD(item['배당락일']);
            if (!date) return acc;
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
        
        // 1. 주차별 데이터셋 생성 (개별 라벨 포함)
        const datasets = [1, 2, 3, 4, 5].map(week => ({
            type: 'bar',
            label: `${week}주차`,
            backgroundColor: weekColors[week],
            data: labels.map(label => monthlyAggregated[label][week]),
            datalabels: {
                display: context => context.dataset.data[context.dataIndex] > 0.0001,
                formatter: (value) => `$${value.toFixed(4)}`,
                color: '#fff',
                font: { size: 15, weight: 'bold' },
                align: 'center',
                anchor: 'center'
            }
        }));
        
        // 2. 총합 표시를 위한 '투명한' 데이터셋 추가
        datasets.push({
            type: 'bar',
            label: 'Total',
            data: new Array(labels.length).fill(0), // 높이가 0인 막대
            backgroundColor: 'transparent',
            datalabels: {
                display: true,
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
                        label: function (context) {
                            if (context.dataset.label === 'Total') return null; // Total 툴팁은 숨김
                            let label = context.dataset.label || '';
                            if (context.parsed.y > 0) {
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
                        filter: (item) => item.datasetIndex < 5 // Total 범례 숨김
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
const breadcrumbItems = computed(() => {
    if (!tickerInfo.value) return [{ label: 'Loading...' }];
    return [
        { label: tickerInfo.value.운용사 },
        { label: tickerInfo.value.티커 }
    ];
});
</script>
<!-- 
    "티커": "LFGY",
    "운용사": "YieldMax",
    "지급주기": "Weekly",
    "Update": "2025-07-08 12:11:09 KST",
    "52Week": "$30.09 - $55.11",
    "Volume": "284,000",
    "AvgVolume": "125,533",
    "NAV": "$40.15",
    "Yield": "N/A",
    "TotalReturn": "N/A"
     -->


<template>
    <div class="card">
        <Breadcrumb :home="home" :model="breadcrumbItems" />

        <div v-if="isLoading" class="flex justify-center items-center h-screen">
            <ProgressSpinner />
        </div>

        <div v-else-if="error" class="text-center mt-8">
            <i class="pi pi-exclamation-triangle text-5xl text-red-500"></i>
            <p class="text-red-500 text-xl mt-4">{{ error }}</p>
        </div>
        
        <div v-else-if="tickerInfo && dividendHistory.length > 0">
            <div class="mt-4">
                <h2>{{ tickerInfo.티커 }} 분배금 정보</h2>
                <p class="text-surface-500 dark:text-surface-400">운용사: {{ tickerInfo.운용사 }} | 지급주기: {{ tickerInfo.지급주기 }}</p>
            </div>

            <div class="card" id="p-chart">
                <Chart type="bar" :data="chartData" :options="chartOptions" :plugins="[ChartDataLabels]" />
            </div>

            <Panel>
                <template #header>
                    <div class="flex justify-between items-center w-full">
                        <div v-if="tickerInfo?.지급주기 === 'Weekly'">
                            <ToggleButton v-model="isPriceChartMode" onLabel="주가 차트" offLabel="배당금 차트"
                                onIcon="pi pi-chart-line" offIcon="pi pi-chart-bar" />
                        </div>
                        <div v-else></div>
                        <SelectButton v-model="selectedTimeRange" :options="timeRangeOptions" aria-labelledby="basic" />
                    </div>
                </template>
                <template #icons>
                    <span class="text-surface-500 dark:text-surface-400">{{ tickerInfo.Update }}</span>
                </template>
                <DataTable :value="dividendHistory" responsiveLayout="scroll" stripedRows scrollable scrollHeight="50vh" :rows="10" paginator>
                    <Column v-for="col in columns" :key="col.field" :field="col.field" :header="col.header" sortable></Column>
                </DataTable>
            </Panel>
        </div>

        <div v-else class="text-center mt-8">
            <i class="pi pi-inbox text-5xl text-surface-500"></i>
            <p class="text-xl mt-4">표시할 데이터가 없습니다.</p>
        </div>
    </div>
</template>