<script setup>
import { ref, onMounted, watch } from 'vue';
import { useRoute } from 'vue-router';

// PrimeVue 컴포넌트 (예: DataTable)
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';

const route = useRoute(); // 현재 라우트 정보 가져오기
const etfData = ref([]);   // 화면에 표시할 데이터
const isLoading = ref(true);

// 모든 ETF 데이터
let allEtfData = null;

// 데이터를 불러오고 현재 경로에 맞게 필터링하는 함수
const fetchDataForRoute = async () => {
  isLoading.value = true;
  try {
    // 1. 전체 데이터가 없으면 한 번만 fetch
    if (!allEtfData) {
      const response = await fetch('/dividends.json'); // public 폴더의 json 로드
      if (!response.ok) throw new Error('Network response was not ok');
      allEtfData = await response.json();
    }
    
    // 2. 현재 경로 이름(name)을 키로 사용해 데이터 추출
    const currentRouteName = route.name; // 'home', 'qdte' 등
    etfData.value = allEtfData[currentRouteName] || []; // 해당 키의 데이터 할당

  } catch (error) {
    console.error("데이터를 불러오는 데 실패했습니다:", error);
    etfData.value = []; // 에러 발생 시 빈 배열로 초기화
  } finally {
    isLoading.value = false;
  }
};

// 컴포넌트가 마운트될 때 데이터 로드
onMounted(() => {
  fetchDataForRoute();
});

// 경로가 변경될 때마다 데이터를 다시 필터링 (SPA의 핵심)
watch(() => route.name, () => {
  // 이미 모든 데이터가 있으므로 다시 fetch할 필요 없음
  if (allEtfData) {
    const currentRouteName = route.name;
    etfData.value = allEtfData[currentRouteName] || [];
  } else {
    // 혹시 모를 예외 처리 (예: 사용자가 직접 url 치고 들어온 경우)
    fetchDataForRoute();
  }
});
</script>

<template>
  <div>
    <div v-if="isLoading">
      데이터를 불러오는 중입니다...
    </div>
    <div v-else>
      <h1>{{ route.name.toUpperCase() }} 분배금 정보</h1>
      <DataTable :value="etfData" responsiveLayout="scroll">
        <Column field="name" header="종목명"></Column>
        <Column field="dividend" header="분배금"></Column>
        <Column field="payment_date" header="지급기준일"></Column>
      </DataTable>
    </div>
  </div>
</template>