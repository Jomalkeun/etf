<script setup>
import { ref, watch, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { joinURL } from 'ufo'; 

// PrimeVue 컴포넌트 (예: DataTable)
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import ProgressSpinner from 'primevue/progressspinner'; // 로딩 인디케이터

const route = useRoute();
const stockData = ref([]);
const isLoading = ref(true);
const error = ref(null);
const ticker = ref(route.params.ticker);

const fetchData = async (tickerName) => {
  isLoading.value = true;
  error.value = null;
  stockData.value = [];
  
  // --- 바로 이 부분입니다! ---
  // public 폴더는 웹 서버의 루트(/) 경로가 됩니다.
  // 따라서 경로는 항상 '/'로 시작해야 가장 안정적입니다.
const url = joinURL(import.meta.env.BASE_URL, `/data/${tickerName.toLowerCase()}.json`);
  console.log('Fetching data from URL:', url); // <--- 디버깅을 위한 로그 추가!

  try {
    const response = await fetch(url);
    
    if (!response.ok) {
      // 404 Not Found 에러인지 확인
      if (response.status === 404) {
        throw new Error(`파일을 찾을 수 없습니다: ${url}`);
      }
      throw new Error(`데이터를 불러올 수 없습니다. (${response.status})`);
    }
    
    stockData.value = await response.json();
  } catch (err) {
    console.error(`Error fetching data for ${tickerName}:`, err);
    error.value = `${tickerName.toUpperCase()}의 분배금 정보를 찾을 수 없습니다. (${err.message})`;
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