<script setup>
import { ref, watch, computed } from 'vue';
import { useRoute } from 'vue-router';
import { joinURL } from 'ufo';

// PrimeVue 및 Chart.js 관련 임포트
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import ProgressSpinner from 'primevue/progressspinner';
import Breadcrumb from 'primevue/breadcrumb';
import Chart from 'primevue/chart';
import SelectButton from 'primevue/selectbutton';
import ChartDataLabels from 'chartjs-plugin-datalabels';

const route = useRoute();
const allStockData = ref([]); // 1. 원본 데이터 전체는 여기에만 저장됩니다.
const isLoading = ref(true);
const error = ref(null);
const ticker = ref(route.params.ticker);

// --- 차트 옵션 ---
const countOptions = ref(['10', '20', 'All']);
const selectedCount = ref('10');
const chartData = ref();
const chartOptions = ref();

// --- DataTable을 위한 동적 컬럼 생성 로직 ---
const columns = computed(() => {
  // 이제 테이블은 항상 전체 데이터를 바라봅니다.
  if (allStockData.value.length === 0) return [];
  return Object.keys(allStockData.value[0]).map(key => ({ field: key, header: key }));
});

// --- 데이터 로딩 함수 (수정 없음) ---
const fetchData = async (tickerName) => {
  isLoading.value = true;
  error.value = null;
  allStockData.value = [];
  
  const url = joinURL(import.meta.env.BASE_URL, `data/${tickerName.toLowerCase()}.json`);

  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`파일을 찾을 수 없습니다.`);
    const rawData = await response.json();

    const dateKey = Object.keys(rawData[0]).find(key => key.toLowerCase().includes('date'));
    allStockData.value = rawData.sort((a, b) => new Date(b[dateKey]) - new Date(a[dateKey]));
  } catch (err) {
    error.value = `${tickerName.toUpperCase()}의 분배금 정보를 찾을 수 없습니다.`;
  } finally {
    isLoading.value = false;
  }
};

// --- 2. 차트 전용 데이터를 만드는 computed 속성 ---
const chartDisplayData = computed(() => {
  if (allStockData.value.length === 0) return [];

  if (selectedCount.value === 'All') {
    return [...allStockData.value]; // 전체 데이터 사용
  }
  // 선택된 개수만큼 최신 데이터 자르기
  return allStockData.value.slice(0, parseInt(selectedCount.value, 10));
});

// --- 차트 데이터/옵션 설정 함수 ---
const setChartData = (data) => {
    const chartReadyData = [...data].reverse(); // 차트 순서를 위해 뒤집음 (과거 -> 현재)
    const documentStyle = getComputedStyle(document.documentElement);

    chartData.value = {
        labels: chartReadyData.map(item => item['배당락'] || item['Ex Date']),
        datasets: [
            {
                type: 'bar',
                label: '배당금',
                backgroundColor: documentStyle.getPropertyValue('--p-cyan-400'),
                data: chartReadyData.map(item => parseFloat((item['배당금'] || item['Amount Paid'])?.replace('$', '') || 0)),
                yAxisID: 'y',
                order: 2, // 막대 차트를 뒤로 보냄
                datalabels: {
                    anchor: 'end',
                    align: 'end',
                    formatter: (value) => value > 0 ? `$${value.toFixed(2)}` : null,
                    color: documentStyle.getPropertyValue('--p-text-color')
                }
            },
            // --- 3. 누락되었던 선형 차트 데이터셋 복원 ---
            {
                type: 'line',
                label: '배당락전일종가',
                borderColor: documentStyle.getPropertyValue('--p-orange-500'),
                borderWidth: 2,
                fill: false,
                tension: 0.4,
                data: chartReadyData.map(item => parseFloat(item['배당락전일종가']?.replace('$', ''))),
                yAxisID: 'y1', // 오른쪽 Y축 사용
                order: 1 // 선형 차트를 앞으로 보냄
            },
            {
                type: 'line',
                label: '배당락일종가',
                borderColor: documentStyle.getPropertyValue('--p-gray-500'),
                borderWidth: 2,
                fill: false,
                tension: 0.4,
                data: chartReadyData.map(item => parseFloat(item['배당락일종가']?.replace('$', ''))),
                yAxisID: 'y1', // 오른쪽 Y축 사용
                order: 1
            }
        ]
    };
};

const setChartOptions = (data) => {
    // ... (이전과 동일, min/max 계산 로직) ...
};

// --- 라우터 및 사용자 선택 감지 로직 ---
watch(() => route.params.ticker, (newTicker) => {
  if (newTicker) {
    selectedCount.value = '10';
    ticker.value = newTicker;
    fetchData(newTicker);
  }
}, { immediate: true });

// chartDisplayData (즉, 사용자의 선택)가 변경될 때마다 차트를 다시 그림
watch(chartDisplayData, (newData) => {
  if (newData.length > 0) {
    setChartData(newData);
    // setChartOptions(newData); // 옵션도 다시 계산하려면 이 주석을 해제
  }
}, { deep: true }); // deep: true 옵션으로 배열 내부의 변경도 감지

// Breadcrumb 로직 (수정 없음)
const home = ref({ icon: 'pi pi-home', route: '/' });
const breadcrumbItems = computed(() => [
  { label: 'ETF 목록', route: '/' },
  { label: ticker.value.toUpperCase() }
]);
</script>

<template>
  <div class="card">
    <Breadcrumb :home="home" :model="breadcrumbItems" />

    <h2 class="mt-4">{{ ticker.toUpperCase() }} 분배금 정보</h2>
    
    <div class="my-4 flex justify-end">
        <SelectButton v-model="selectedCount" :options="countOptions" aria-labelledby="basic" />
    </div>

    <div class="card" id="p-chart" v-if="!isLoading && allStockData.length > 0">
        <Chart type="bar" :data="chartData" :options="chartOptions" :plugins="[ChartDataLabels]" />
    </div>

    <div v-if="isLoading" class="flex justify-center items-center h-48">
      <ProgressSpinner />
    </div>
    <div v-else-if="error">
      <p class="text-red-500">{{ error }}</p>
    </div>
    
    <!-- 1. DataTable은 항상 원본 데이터 전체(allStockData)를 바라봅니다. -->
    <template v-else-if="allStockData.length > 0">
      <DataTable :value="allStockData" responsiveLayout="scroll" stripedRows scrollable scrollHeight="50vh">
        <Column v-for="col in columns" :key="col.field" :field="col.field" :header="col.header"></Column>
      </DataTable>
    </template>
    
    <div v-else>
      <p>표시할 데이터가 없습니다.</p>
    </div>
  </div>
</template>