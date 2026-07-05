import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import Layout from './components/Layout.jsx';
import Dashboard from './pages/Dashboard.jsx';
import IngestionCreate from './pages/IngestionCreate.jsx';
import IngestionBatchList from './pages/IngestionBatchList.jsx';
import IngestionBatchDetail from './pages/IngestionBatchDetail.jsx';
import GoldenSearch from './pages/GoldenSearch.jsx';
import GoldenDetail from './pages/GoldenDetail.jsx';
import SourceSearch from './pages/SourceSearch.jsx';
import SourceDetail from './pages/SourceDetail.jsx';
import MatchCandidateDetail from './pages/MatchCandidateDetail.jsx';
import ManualReviewQueue from './pages/ManualReviewQueue.jsx';
import ManualReviewDetail from './pages/ManualReviewDetail.jsx';
import DuplicateGoldenQueue from './pages/DuplicateGoldenQueue.jsx';
import GoldenMergeReview from './pages/GoldenMergeReview.jsx';
import MatchingFeatureSettings from './pages/MatchingFeatureSettings.jsx';
import MatchingRuleList from './pages/MatchingRuleList.jsx';
import MatchingRuleDetail from './pages/MatchingRuleDetail.jsx';
import RuleSimulation from './pages/RuleSimulation.jsx';
import ThresholdSettings from './pages/ThresholdSettings.jsx';
import SurvivorshipRuleList from './pages/SurvivorshipRuleList.jsx';
import SurvivorshipRuleDetail from './pages/SurvivorshipRuleDetail.jsx';
import SurvivorshipPreview from './pages/SurvivorshipPreview.jsx';
import SourceSystemList from './pages/SourceSystemList.jsx';
import AuditHistory from './pages/AuditHistory.jsx';

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/dashboard" element={<Navigate to="/" replace />} />
          <Route path="/ingestion/new" element={<IngestionCreate />} />
          <Route path="/ingestion/batches" element={<IngestionBatchList />} />
          <Route path="/ingestion/batches/:batchId" element={<IngestionBatchDetail />} />
          <Route path="/golden" element={<GoldenSearch />} />
          <Route path="/golden/:goldenId" element={<GoldenDetail />} />
          <Route path="/sources" element={<SourceSearch />} />
          <Route path="/sources/:sourceRecordId" element={<SourceDetail />} />
          <Route path="/match-candidates/:candidateId" element={<MatchCandidateDetail />} />
          <Route path="/manual-review" element={<ManualReviewQueue />} />
          <Route path="/manual-review/:taskId" element={<ManualReviewDetail />} />
          <Route path="/duplicates" element={<DuplicateGoldenQueue />} />
          <Route path="/duplicates/:duplicateId" element={<GoldenMergeReview />} />
          <Route path="/settings/matching-features" element={<MatchingFeatureSettings />} />
          <Route path="/settings/matching-rules" element={<MatchingRuleList />} />
          <Route path="/settings/matching-rules/:ruleId" element={<MatchingRuleDetail />} />
          <Route path="/settings/rule-simulation" element={<RuleSimulation />} />
          <Route path="/settings/thresholds" element={<ThresholdSettings />} />
          <Route path="/settings/survivorship" element={<SurvivorshipRuleList />} />
          <Route path="/settings/survivorship/:ruleId" element={<SurvivorshipRuleDetail />} />
          <Route path="/settings/survivorship-preview" element={<SurvivorshipPreview />} />
          <Route path="/settings/source-systems" element={<SourceSystemList />} />
          <Route path="/audit" element={<AuditHistory />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
