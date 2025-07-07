<script setup>
import { ref, watch, computed } from 'vue';
import { useRoute } from 'vue-router';
import { joinURL } from 'ufo';

// PrimeVue 컴포넌트
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import ProgressSpinner from 'primevue/progressspinner';
import Breadcrumb from 'primevue/breadcrumb';
import Chart from 'primevue/chart'; // Chart 컴포넌트 임포트

const route = useRoute();
const stockData = ref([]);
const isLoading = ref(true);
const error = ref(null);
const ticker = ref(route.params.ticker);

// --- 차트 관련 반응형 데이터 ---
const chartData = ref();
const chartOptions = ref();

// --- DataTable을 위한 동적 컬럼 생성 로직 (수정 없음) ---
const columns = computed(() => {
  if (stockData.value.length === 0) return [];
  return Object.keys(stockData.value[0]).map(key => ({ field: key, header: key }));
});

// --- 데이터 로딩 및 차트 데이터 설정 함수 ---
const fetchData = async (tickerName) => {
  isLoading.value = true;
  error.value = null;
  stockData.value = [];
  chartData.value = null; // 데이터를 새로 불러올 때 차트 초기화

  const url = joinURL(import.meta.env.BASE_URL, `data/${tickerName.toLowerCase()}.json`);
  console.log('Fetching data from URL:', url);

  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`파일을 찾을 수 없습니다: ${url} (${response.status})`);
    }
    const rawData = await response.json();

    // 1. 날짜 기준으로 데이터를 정렬 (최신 데이터가 위로 오도록)
    const dateKey = Object.keys(rawData[0]).find(key => key.toLowerCase().includes('date'));
    const sortedData = rawData.sort((a, b) => new Date(b[dateKey]) - new Date(a[dateKey]));

    // 2. 정렬된 데이터를 stockData에 할당
    stockData.value = sortedData;

    // 3. 차트 데이터 설정 함수 호출
    setChartData(sortedData);
    setChartOptions();

  } catch (err) {
    console.error(`Error fetching data for ${tickerName}:`, err);
    error.value = `${tickerName.toUpperCase()}의 분배금 정보를 찾을 수 없습니다.`;
  } finally {
    isLoading.value = false;
  }
};

// 날짜 형식을 'YY.MM.DD'로 변환하는 헬퍼 함수
const formatDate = (dateString) => {
  if (!dateString || dateString.toLowerCase() === 'n/a') {
    return 'N/A';
  }
  try {
    const date = new Date(dateString);
    const year = date.getFullYear().toString().slice(-2); // 마지막 두 자리
    const month = (date.getMonth() + 1).toString().padStart(2, '0'); // 0 채우기
    const day = date.getDate().toString().padStart(2, '0'); // 0 채우기
    return `${year}.${month}.${day}`;
  } catch (error) {
    return dateString; // 변환 실패 시 원본 반환
  }
};

// --- 차트 데이터 가공 및 설정 함수 (모든 기능 추가) ---
const setChartData = (data) => {
  const latestData = data.slice(0, 10).reverse();
  const documentStyle = getComputedStyle(document.documentElement);

  chartData.value = {
    labels: latestData.map(item => formatDate(item['배당락'] || item['Ex Date'])), // 날짜 형식 변경 적용
    datasets: [
      {
        type: 'bar',
        label: '배당금',
        backgroundColor: documentStyle.getPropertyValue('--p-cyan-500'),
        data: latestData.map(item => parseFloat((item['배당금'] || item['Amount Paid'])?.replace('$', ''))),
        yAxisID: 'y'
      },
      {
        type: 'line',
        label: '배당락전일종가',
        borderColor: documentStyle.getPropertyValue('--p-orange-500'),
        borderWidth: 2,
        fill: false,
        tension: 0.4,
        data: latestData.map(item => parseFloat(item['배당락전일종가']?.replace('$', ''))),
        yAxisID: 'y1'
      },
      {
        type: 'line',
        label: '배당락일종가',
        borderColor: documentStyle.getPropertyValue('--p-gray-500'),
        borderWidth: 2,
        fill: false,
        tension: 0.4,
        data: latestData.map(item => parseFloat(item['배당락일종가']?.replace('$', ''))),
        yAxisID: 'y1'
      }
    ]
  };
};

const setChartOptions = () => {
  // 1. 차트에 표시될 모든 숫자 데이터를 가져옵니다.
  const allNumericData = chartData.value.datasets.flatMap(dataset => dataset.data).filter(val => !isNaN(val));
  const priceData = [
    ...chartData.value.datasets[1].data, // 배당락전일종가
    ...chartData.value.datasets[2].data  // 배당락일종가
  ].filter(val => !isNaN(val));

  // 2. Y축의 min/max 값을 계산합니다. (데이터가 있을 경우에만)
  const yMin = priceData.length > 0 ? Math.min(...priceData) * 0.98 : 0; // 최소값보다 2% 낮게
  const yMax = priceData.length > 0 ? Math.max(...priceData) * 1.02 : 1; // 최대값보다 2% 높게

  const documentStyle = getComputedStyle(document.documentElement);
  const textColor = documentStyle.getPropertyValue('--p-text-color');
  const textColorSecondary = documentStyle.getPropertyValue('--p-text-muted-color');
  const surfaceBorder = documentStyle.getPropertyValue('--p-content-border-color');

  chartOptions.value = {
    maintainAspectRatio: false,
    aspectRatio: 0.6,
    plugins: {
      // 3. 데이터 값을 차트 위에 표시하는 'datalabels' 플러그인 설정
      datalabels: {
        align: 'end',
        anchor: 'end',
        color: textColorSecondary,
        font: { size: 10 },
        formatter: (value, context) => {
          // 바(bar) 차트(배당금)에만 값을 표시하도록 설정
          if (context.dataset.type === 'bar') {
            return '$' + value.toFixed(4); // 소수점 4자리까지 표시
          }
          return null; // 라인 차트에는 표시하지 않음
        }
      },
      legend: { labels: { color: textColor } },
      tooltip: { /* 이전과 동일 */ }
    },
    scales: {
      x: { /* 이전과 동일 */ },
      y: { // 왼쪽 Y축 (배당금)
        type: 'linear', display: true, position: 'left',
        ticks: { color: textColorSecondary },
        grid: { color: surfaceBorder }
      },
      y1: { // 오른쪽 Y축 (주가)
        type: 'linear', display: true, position: 'right',
        // 4. 계산된 min/max 값을 Y축에 적용
        min: yMin,
        max: yMax,
        ticks: { color: textColorSecondary },
        grid: { drawOnChartArea: false, color: surfaceBorder }
      }
    }
  };
};

// --- Breadcrumb 반응성 로직 (수정 없음) ---
const home = ref({ icon: 'pi pi-home', route: '/' });
const breadcrumbItems = computed(() => [
  { label: 'ETF 목록', route: '/' },
  { label: ticker.value.toUpperCase() }
]);

// --- 라우터 변경 감지 로직 (수정 없음) ---
watch(() => route.params.ticker, (newTicker) => {
  if (newTicker) {
    ticker.value = newTicker;
    fetchData(newTicker);
  }
}, { immediate: true });
</script>

<template>
  <div class="card">
    <Breadcrumb :home="home" :model="breadcrumbItems">
      <!-- Breadcrumb 템플릿 부분은 생략 -->
    </Breadcrumb>

    <h2 class="mt-4">{{ ticker.toUpperCase() }} 분배금 정보</h2>

    <!-- 차트는 로딩이 끝나고 데이터가 있을 때만 보여줌 -->
    <div class="card" id="p-chart" v-if="!isLoading && chartData">
      <Chart type="bar" :data="chartData" :options="chartOptions" />
    </div>

    <!-- 로딩 및 에러 처리 (수정 없음) -->
    <div v-if="isLoading" class="flex justify-center items-center h-48">
      <ProgressSpinner />
    </div>
    <div v-else-if="error">
      <p class="text-red-500">{{ error }}</p>
    </div>

    <!-- 데이터 테이블 (수정 없음) -->
    <template v-else-if="stockData.length > 0">
      <DataTable :value="stockData" responsiveLayout="scroll" stripedRows scrollable scrollHeight="50vh">
        <!-- v-for를 사용해 동적으로 컬럼을 렌더링합니다. -->
        <Column v-for="col in columns" :key="col.field" :field="col.field" :header="col.header">
          <!-- 1. 컬럼 헤더에 'date' 또는 '날짜' 관련 단어가 포함되어 있는지 확인 -->
          <template #body="slotProps"
            v-if="col.header.toLowerCase().includes('date') || ['배당공시', '배당락', '주주확정', '배당지급일'].includes(col.header)">
            <!-- 2. 포함되어 있다면, formatDate 함수를 적용하여 표시 -->
            <span>{{ formatDate(slotProps.data[col.field]) }}</span>
          </template>
          <!-- 3. 날짜가 아닌 다른 데이터는 그대로 표시 (이 부분은 수정 없음) -->
        </Column>
      </DataTable>
    </template>
    <div v-else>
      <p>표시할 데이터가 없습니다.</p>
    </div>
  </div>
</template>