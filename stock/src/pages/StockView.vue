<script setup>
import { ref, watch, computed } from 'vue';
import { useRoute } from 'vue-router';
import { joinURL } from 'ufo';

// PrimeVue 및 Chart.js 관련 임포트
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import ProgressSpinner from 'primevue/progressspinner';
import Breadcrumb from 'primevue/breadcrumb';
import SelectButton from 'primevue/selectbutton';
import Chart from 'primevue/chart';
import ChartDataLabels from 'chartjs-plugin-datalabels';

const route = useRoute();
const tickerInfo = ref(null);
const dividendHistory = ref([]); // 전체 배당 기록 (최신순)
const isLoading = ref(true);
const error = ref(null);

// --- 1. UI 제어 상태 변경 ---
const timeRangeOptions = ref(['1Y', '2Y', '3Y', 'Max']); // 옵션 변경
const selectedTimeRange = ref('1Y'); // 기본값은 '1Y'

const chartData = ref();
const chartOptions = ref();

// --- 데이터 로딩 및 가공 함수 ---
const fetchData = async (tickerName) => {
  isLoading.value = true;
  error.value = null;
  tickerInfo.value = null;
  dividendHistory.value = [];

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

  } catch (err) {
    error.value = `${tickerName.toUpperCase()}의 분배금 정보를 찾을 수 없습니다.`;
  } finally {
    isLoading.value = false;
  }
};

// --- DataTable을 위한 동적 컬럼 생성 ---
const columns = computed(() => {
  if (dividendHistory.value.length === 0) return [];
  return Object.keys(dividendHistory.value[0]).map(key => ({ field: key, header: key }));
});

// --- 2. 차트 전용 데이터를 '시간 범위' 기준으로 필터링 (핵심 수정) ---
const chartDisplayData = computed(() => {
  if (dividendHistory.value.length === 0) return [];
  
  if (selectedTimeRange.value === 'Max') {
    return [...dividendHistory.value].reverse(); // 전체 데이터 (시간 순으로 뒤집음)
  }

  // 기준 날짜 계산
  const now = new Date();
  const years = parseInt(selectedTimeRange.value.replace('Y', ''), 10);
  // 오늘로부터 N년 전의 날짜를 계산
  const cutoffDate = new Date(now.setFullYear(now.getFullYear() - years));

  // 원본 데이터(최신순)에서 기준 날짜 이후의 데이터만 필터링
  const filteredData = dividendHistory.value.filter(item => {
    const itemDate = new Date(item['배당락일']);
    return itemDate >= cutoffDate;
  });
  
  // 차트 표시를 위해 시간 순으로 뒤집음 (과거 -> 현재)
  return filteredData.reverse();
});


// --- 3. setChartDataAndOptions (수정 없음, 그대로 작동) ---
// 이 함수는 이미 전달받은 데이터를 기반으로 차트를 그리므로,
// chartDisplayData가 올바른 데이터만 넘겨주면 알아서 잘 작동합니다.
const setChartDataAndOptions = (data, frequency) => {
    const documentStyle = getComputedStyle(document.documentElement);
    const textColor = documentStyle.getPropertyValue('--p-text-color');
    const textColorSecondary = documentStyle.getPropertyValue('--p-text-muted-color');
    const surfaceBorder = documentStyle.getPropertyValue('--p-content-border-color');

    if (frequency === 'Weekly') {
        const monthlyAggregated = data.reduce((acc, item) => {
            const date = new Date(item['배당락일']);
            const yearMonth = `${date.getFullYear().toString().slice(-2)}.${(date.getMonth() + 1).toString().padStart(2, '0')}`;
            const amount = parseFloat(item['배당금']?.replace('$', '') || 0);
            const weekOfMonth = Math.floor((date.getDate() - 1) / 7) + 1;

            if (!acc[yearMonth]) {
                acc[yearMonth] = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 };
            }
            acc[yearMonth][weekOfMonth] += amount;
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
                formatter: (value) => value > 0 ? `$${value.toFixed(4)}` : null,
                color: '#fff', font: { size: 10 }
            }
        }));
        
        chartData.value = { labels, datasets };
        chartOptions.value = {
            maintainAspectRatio: false, aspectRatio: 0.8,
            plugins: {
                title: { display: true, text: '월별 주차 배당금 누적' },
                tooltip: {
                    mode: 'index',
                    callbacks: {
                        footer: (tooltipItems) => {
                            let sum = tooltipItems.reduce((a, b) => a + b.parsed.y, 0);
                            return 'Total: $' + sum.toFixed(4);
                        },
                    },
                },
                datalabels: { display: true }
            },
            scales: {
                x: { stacked: true, ticks: { color: textColorSecondary }, grid: { color: surfaceBorder } },
                y: { stacked: true, ticks: { color: textColorSecondary }, grid: { color: surfaceBorder } }
            }
        };

    } else { // Monthly 또는 다른 주기의 경우
        // --- 2. 누락되었던 콤보 차트 로직 복원 ---
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
                    data: data.map(item => parseFloat(item['배당락전일종가']?.replace('$', '')))
                },
                {
                    type: 'line', label: '배당락일종가', yAxisID: 'y1', order: 1,
                    borderColor: documentStyle.getPropertyValue('--p-gray-500'),
                    data: data.map(item => parseFloat(item['배당락일종가']?.replace('$', '')))
                }
            ]
        };
        chartOptions.value = {
            maintainAspectRatio: false, aspectRatio: 0.6,
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

// --- 라우터 및 UI 상호작용 감지 ---
watch(() => route.params.ticker, (newTicker) => {
  if (newTicker) {
    selectedTimeRange.value = '1Y'; // 페이지 이동 시 기본값으로 리셋
    fetchData(newTicker);
  }
}, { immediate: true });

// chartDisplayData가 변경될 때마다 차트를 다시 그림
watch(chartDisplayData, (newData) => {
  if (newData && newData.length > 0 && tickerInfo.value) {
    setChartDataAndOptions(newData, tickerInfo.value.지급주기);
  } else {
    chartData.value = null;
    chartOptions.value = null;
  }
}, { deep: true, immediate: true });

// 사용자가 SelectButton을 클릭하면 chartDisplayData가 자동으로 재계산되고,
// 위의 watch가 실행되어 차트가 업데이트됩니다.
// 따라서 별도의 watch(selectedTimeRange, ...)는 필요 없습니다.

// Breadcrumb 데이터
const home = ref({ icon: 'pi pi-home', route: '/' });
const breadcrumbItems = computed(() => [
  { label: 'ETF 목록', route: '/' },
  { label: tickerInfo.value ? `${tickerInfo.value.운용사} - ${tickerInfo.value.티커}` : 'Loading...' }
]);
</script>

<template>
  <div class="card">
    <Breadcrumb :home="home" :model="breadcrumbItems" />

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
        <div class="my-4 flex justify-end">
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