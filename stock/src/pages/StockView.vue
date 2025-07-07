<script setup>
import { ref, watch, onMounted } from 'vue';
import { useRoute } from 'vue-router';

// PrimeVue 컴포넌트 (예: DataTable)
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import ProgressSpinner from 'primevue/progressspinner'; // 로딩 인디케이터

const route = useRoute();
const stockData = ref([]);
const isLoading = ref(true);
const error = ref(null);
const ticker = ref(route.params.ticker);

// 데이터를 불러오는 비동기 함수
const fetchData = async (tickerName) => {
  isLoading.value = true;
  error.value = null;
  stockData.value = [];
  
  try {
    // 동적으로 JSON 파일 경로 생성
    const response = await fetch(`/data/${tickerName.toLowerCase()}.json`);
    
    if (!response.ok) {
      throw new Error(`데이터를 불러올 수 없습니다. (${response.status})`);
    }
    
    stockData.value = await response.json();
  } catch (err) {
    console.error(`Error fetching data for ${tickerName}:`, err);
    error.value = `${tickerName.toUpperCase()}의 분배금 정보를 찾을 수 없습니다.`;
  } finally {
    isLoading.value = false;
  }
};

// URL의 :ticker 파라미터가 변경될 때마다 데이터를 다시 불러옴
watch(() => route.params.ticker, (newTicker) => {
  if (newTicker) {
    ticker.value = newTicker;
    fetchData(newTicker);
  }
});

// 컴포넌트가 처음 마운트될 때 데이터 로드
onMounted(() => {
  fetchData(ticker.value);
});
</script>

<template>
  <div class="card">
    <h2>{{ ticker.toUpperCase() }} 분배금 정보</h2>
    
    <div v-if="isLoading" class="p-d-flex p-jc-center p-ai-center" style="height: 200px;">
      <ProgressSpinner />
    </div>
    
    <div v-else-if="error">
      <p style="color: red;">{{ error }}</p>
    </div>
    
    <DataTable v-else :value="stockData" responsiveLayout="scroll">
      <!-- 데이터 구조에 맞게 컬럼을 동적으로 생성하거나, 고정할 수 있습니다 -->
      <!-- 예시: Roundhill -->
      <Column field="Declaration" header="Declaration"></Column>
      <Column field="Ex Date" header="Ex Date"></Column>
      <Column field="Record Date" header="Record Date"></Column>
      <Column field="Pay Date" header="Pay Date"></Column>
      <Column field="Amount Paid" header="Amount Paid"></Column>
    </DataTable>
  </div>
</template>