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
import ToggleButton from 'primevue/togglebutton'; // ToggleButton 임포트

const route = useRoute();
const tickerInfo = ref(null);
const dividendHistory = ref([]); // 전체 배당 기록 (최신순)
const isLoading = ref(true);
const error = ref(null);

// --- 1. UI 제어 상태: 이제 timeRangeOptions는 동적으로 생성됨 ---
const timeRangeOptions = ref([]); // 초기에는 비어있음
const selectedTimeRange = ref('1Y'); // 기본값은 유지
const isPriceChartMode = ref(false); // 1. 차트 모드 상태 추가 (기본값: 배당금)

const chartData = ref();
const chartOptions = ref();

// --- 데이터 로딩 및 가공 함수 ---
const fetchData = async (tickerName) => {
  isLoading.value = true;
  error.value = null;
  tickerInfo.value = null;
  dividendHistory.value = [];
  timeRangeOptions.value = []; // 데이터를 새로 불러올 때 옵션 초기화

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
    
    // --- 2. 데이터 로드 후, 동적으로 시간 범위 옵션 생성 ---
    generateDynamicTimeRangeOptions();

  } catch (err) {
    error.value = `${tickerName.toUpperCase()}의 분배금 정보를 찾을 수 없습니다.`;
  } finally {
    isLoading.value = false;
  }
};

// --- 동적으로 시간 범위 옵션을 생성하는 함수 (NEW!) ---
const generateDynamicTimeRangeOptions = () => {
    if (dividendHistory.value.length === 0) {
        timeRangeOptions.value = [];
        return;
    }

    // 가장 오래된 배당 기록의 날짜를 가져옴
    const oldestRecordDate = new Date(dividendHistory.value[dividendHistory.value.length - 1]['배당락일']);
    const now = new Date();
    
    const options = [];
    const oneYearAgo = new Date(new Date().setFullYear(now.getFullYear() - 1));
    const twoYearsAgo = new Date(new Date().setFullYear(now.getFullYear() - 2));
    const threeYearsAgo = new Date(new Date().setFullYear(now.getFullYear() - 3));

    // 운용 기간이 1년 이상이면 '1Y' 옵션 추가
    if (oldestRecordDate < oneYearAgo) {
        options.push('1Y');
    }
    // 운용 기간이 2년 이상이면 '2Y' 옵션 추가
    if (oldestRecordDate < twoYearsAgo) {
        options.push('2Y');
    }
    // 운용 기간이 3년 이상이면 '3Y' 옵션 추가
    if (oldestRecordDate < threeYearsAgo) {
        options.push('3Y');
    }
    
    // 'Max' 옵션은 항상 추가
    options.push('Max');

    timeRangeOptions.value = options;

    // 만약 기본 선택값('1Y')이 생성된 옵션에 없다면, 첫 번째 옵션으로 변경
    if (!options.includes(selectedTimeRange.value)) {
        selectedTimeRange.value = options[0] || 'Max';
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


// --- 차트 데이터/옵션 설정 함수 (최종 버전) ---
const setChartDataAndOptions = (data, frequency) => {
    const documentStyle = getComputedStyle(document.documentElement);
    const textColor = documentStyle.getPropertyValue('--p-text-color');
    const textColorSecondary = documentStyle.getPropertyValue('--p-text-muted-color');
    const surfaceBorder = documentStyle.getPropertyValue('--p-content-border-color');

    // 3. Weekly 이면서, 주가 차트 모드일 때를 위한 새로운 로직
    if (frequency === 'Weekly' && isPriceChartMode.value) {
        // --- 주가 추이 선형 차트 (Weekly) ---
        chartData.value = {
            labels: data.map(item => item['배당락일']), // 각 배당락일이 X축
            datasets: [
                {
                    type: 'line', label: '배당락전일종가',
                    borderColor: documentStyle.getPropertyValue('--p-orange-500'),
                    data: data.map(item => parseFloat(item['배당락전일종가']?.replace('$', ''))),
                },
                {
                    type: 'line', label: '배당락일종가',
                    borderColor: documentStyle.getPropertyValue('--p-gray-500'),
                    data: data.map(item => parseFloat(item['배당락일종가']?.replace('$', '')))
                }
            ]
        };
        chartOptions.value = {
            maintainAspectRatio: false, aspectRatio: 0.8,
            plugins: { title: { display: true, text: '주가 추이' }, legend: { labels: { color: textColor } } },
            scales: {
                x: { ticks: { color: textColorSecondary }, grid: { color: surfaceBorder } },
                y: { ticks: { color: textColorSecondary }, grid: { color: surfaceBorder } }
            }
        };

    } else if (frequency === 'Weekly') {
        // --- 월별 누적 배당금 막대 차트 (Weekly) ---
        const monthlyAggregated = data.reduce((acc, item) => {
            const date = new Date(item['배당락일']);
            const yearMonth = `${date.getFullYear().toString().slice(-2)}.${(date.getMonth() + 1).toString().padStart(2, '0')}`;
            const amount = parseFloat(item['배당금']?.replace('$', '') || 0);
            const weekOfMonth = Math.floor((date.getDate() - 1) / 7) + 1;
            if (!acc[yearMonth]) { acc[yearMonth] = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 }; }
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
              x: { stacked: true, ticks: { color: textColorSecondary } }, 
              y: { stacked: true, ticks: { color: textColorSecondary } } }
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
    isPriceChartMode.value = false; // 다른 티커로 이동 시 항상 배당금 모드로 리셋
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

// 4. 토글 버튼 상태가 바뀔 때도 차트를 다시 그리도록 watch 추가
watch(isPriceChartMode, () => {
    // chartDisplayData는 변하지 않으므로, 현재 데이터를 가지고 차트만 다시 그리면 됨
    if (chartDisplayData.value && chartDisplayData.value.length > 0 && tickerInfo.value) {
        setChartDataAndOptions(chartDisplayData.value, tickerInfo.value.지급주기);
    }
});

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
        <!-- UI 컨트롤 영역 -->
        <div class="my-4 flex justify-between items-center">
            <!-- 토글 버튼 (Weekly ETF일 때만 보임) -->
            <div v-if="tickerInfo?.지급주기 === 'Weekly'">
                <ToggleButton v-model="isPriceChartMode" onLabel="주가 차트" offLabel="배당금 차트" 
                              onIcon="pi pi-chart-line" offIcon="pi pi-chart-bar" />
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