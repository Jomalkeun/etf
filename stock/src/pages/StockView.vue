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

// --- 데이터 상태 관리 ---
const tickerInfo = ref(null);         // 티커의 고유 정보 (운용사, 지급주기 등)
const dividendHistory = ref([]);    // 전체 배당 기록 (항상 최신순으로 정렬)
const isLoading = ref(true);
const error = ref(null);

// --- UI 제어 상태 ---
const countOptions = ref(['10', '20', 'All']);
const selectedCount = ref('10');

// --- 차트 데이터 ---
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
    
    // 배당 기록을 날짜 기준으로 내림차순 정렬 (최신 데이터가 맨 위로)
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
  // 이제 dividendHistory의 첫 번째 아이템을 기준으로 컬럼을 만듭니다.
  return Object.keys(dividendHistory.value[0]).map(key => ({ field: key, header: key }));
});

// --- 차트 표시용 데이터 (사용자 선택에 따라 동적으로 변경) ---
const chartDisplayData = computed(() => {
  if (dividendHistory.value.length === 0) return [];
  if (selectedCount.value === 'All') {
    return [...dividendHistory.value].reverse(); // 차트는 시간 순(과거->현재)이므로 뒤집음
  }
  const count = parseInt(selectedCount.value, 10);
  // 최신 데이터 N개를 잘라낸 후, 시간 순으로 뒤집음
  return dividendHistory.value.slice(0, count).reverse();
});

// --- 차트 데이터/옵션 설정 함수 ---
const setChartData = (data) => {
    const documentStyle = getComputedStyle(document.documentElement);
    chartData.value = {
        labels: data.map(item => item['배당락일']), // YY.MM.DD 형식 변환은 scraper에서 미리 처리하는 것이 더 효율적
        datasets: [
            {
                type: 'bar',
                label: '배당금',
                backgroundColor: documentStyle.getPropertyValue('--p-cyan-400'),
                data: data.map(item => parseFloat(item['배당금']?.replace('$', '') || 0)),
                yAxisID: 'y', order: 2,
                datalabels: {
                    anchor: 'end', align: 'end',
                    formatter: (value) => value > 0 ? `$${value.toFixed(2)}` : null,
                    color: documentStyle.getPropertyValue('--p-text-color'),
                    font: { weight: 'bold' }
                }
            },
            {
                type: 'line',
                label: '배당락전일종가',
                borderColor: documentStyle.getPropertyValue('--p-orange-500'),
                data: data.map(item => parseFloat(item['배당락전일종가']?.replace('$', ''))),
                yAxisID: 'y1', order: 1
            },
            {
                type: 'line',
                label: '배당락일종가',
                borderColor: documentStyle.getPropertyValue('--p-gray-500'),
                data: data.map(item => parseFloat(item['배당락일종가']?.replace('$', ''))),
                yAxisID: 'y1', order: 1
            }
        ]
    };
};

const setChartOptions = (data) => {
    const documentStyle = getComputedStyle(document.documentElement);
    const textColor = documentStyle.getPropertyValue('--p-text-color');
    const prices = data.flatMap(item => [
        parseFloat(item['배당락전일종가']?.replace('$', '')),
        parseFloat(item['배당락일종가']?.replace('$', ''))
    ]).filter(p => !isNaN(p));
    if (prices.length === 0) {
        chartOptions.value = { maintainAspectRatio: false, aspectRatio: 0.6 };
        return;
    }
    const priceMin = Math.min(...prices) * 0.98;
    const priceMax = Math.max(...prices) * 1.02;

    chartOptions.value = {
        maintainAspectRatio: false,
        aspectRatio: 0.6,
        plugins: {
            datalabels: { display: context => context.dataset.type === 'bar' && context.dataset.data[context.dataIndex] > 0 },
            legend: { labels: { color: textColor } },
            tooltip: { /* 툴팁 콜백 로직 */ }
        },
        scales: {
            x: { /* x축 옵션 */ },
            y: { /* 왼쪽 y축 옵션 */ },
            y1: {
                type: 'linear', display: true, position: 'right',
                min: priceMin, max: priceMax,
                /* 나머지 y1축 옵션 */
            }
        }
    };
};

// --- 라우터 및 UI 상호작용 감지 ---
watch(() => route.params.ticker, (newTicker) => {
  if (newTicker) {
    selectedCount.value = '10'; // 페이지 이동 시 기본값으로 리셋
    fetchData(newTicker);
  }
}, { immediate: true });

watch(chartDisplayData, (newData) => {
  if (newData && newData.length > 0) {
    setChartData(newData);
    setChartOptions(newData);
  } else {
    chartData.value = null;
    chartOptions.value = null;
  }
}, { deep: true, immediate: true });


// Breadcrumb 데이터
const home = ref({ icon: 'pi pi-home', route: '/' });
const breadcrumbItems = computed(() => [
  { label: 'ETF 목록', route: '/' },
  // tickerInfo가 로드된 후에만 라벨을 표시하도록 함
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
        <div class="my-4 flex justify-end">
            <SelectButton v-model="selectedCount" :options="countOptions" aria-labelledby="basic" />
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