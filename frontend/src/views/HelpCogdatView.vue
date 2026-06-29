<template>
  <div class="container-fluid">
    <div class="mb-5">
      <h1 class="text-center">Help: COGDAT Metadata Columns</h1>
      <!-- <p class="lead">Description of columns present in the COGDAT metadata CSV.</p> -->
    </div>

    <div class="table-responsive">
      <table class="table table-striped table-bordered details-table">
        <thead class="thead-dark">
          <tr>
            <th>Column</th>
            <th>Description</th>
          </tr>
        </thead>
        <tbody>
          <tr><td>sampleID</td><td>Internal sample identifier used in COGDAT exports.</td></tr>
          <tr><td>plateID</td><td>Laboratory plate or batch identifier.</td></tr>
          <tr><td>sequenceupdated</td><td>Timestamp when sequence data was last updated.</td></tr>
          <tr><td>Ns</td><td>Number of ambiguous bases (N) in the consensus sequence.</td></tr>
          <tr><td>pangolin</td><td>Pangolin lineage assigned to the sequence.</td></tr>
          <tr><td>runsstatus</td><td>Status of the sequencing run (e.g., Finished).</td></tr>
          <tr><td>processingstatus</td><td>Processing workflow status for the sample.</td></tr>
          <tr><td>lastpushed</td><td>Timestamp when the record was last pushed to downstream systems.</td></tr>
          <tr><td>finalized</td><td>Flag indicating whether sequence is finalized (1 = yes).</td></tr>
          <tr><td>pseudonym_prefix</td><td>Prefix used when pseudonymising sample IDs.</td></tr>
          <tr><td>pseudonym_numerical</td><td>Numeric part of the pseudonymised identifier.</td></tr>
          <tr><td>HHU_id</td><td>Local HHU (laboratory) identifier for the sample.</td></tr>
          <tr><td>GISAIDuploaded</td><td>Flag indicating whether sequence was uploaded to GISAID.</td></tr>
          <tr><td>GISAIDuploadedtimestamp</td><td>Timestamp for GISAID upload.</td></tr>
          <tr><td>GISAIDISL</td><td>GISAID ISL accession assigned to the sequence (if any).</td></tr>
          <tr><td>GISAIDupload_givenUp</td><td>Flag indicating upload attempts to GISAID were abandoned.</td></tr>
          <tr><td>pangolin_recent</td><td>Most recent pangolin lineage (updated field).</td></tr>
          <tr><td>sequenceAnalysisTimestamp</td><td>When the sequence analysis pipeline ran.</td></tr>
          <tr><td>addedToTableTimestamp</td><td>When the record was added to the COGDAT table.</td></tr>
          <tr><td>firstSequenceTimestamp</td><td>Timestamp for the first available sequence for this sample.</td></tr>
          <tr><td>firstSequenceFewer3000NsTimestamp</td><td>First sequence timestamp with &lt;3000 Ns.</td></tr>
          <tr><td>arrivalAtVirologyDate</td><td>Date the sample arrived at the virology lab.</td></tr>
          <tr><td>RKIUploadAttempted</td><td>Flag indicating an attempt to upload to RKI was made.</td></tr>
          <tr><td>RKIRejected</td><td>Flag indicating RKI rejected the submission.</td></tr>
          <tr><td>RKIUploadedTimestamp</td><td>Timestamp for RKI upload if applicable.</td></tr>
          <tr><td>RKIIMSID</td><td>RKI IMS identifier associated with the upload.</td></tr>
          <tr><td>rawData_ENA_uploaded</td><td>Flag showing whether raw reads were uploaded to ENA.</td></tr>
          <tr><td>rawData_ENA_uploadGivenUp</td><td>Flag if ENA upload attempts were abandoned.</td></tr>
          <tr><td>rawData_ENA_uploadTimestamp</td><td>Timestamp of ENA raw data upload.</td></tr>
          <tr><td>rawData_ENA_sample_accession</td><td>ENA sample accession (if uploaded).</td></tr>
          <tr><td>rawData_ENA_run_accession</td><td>ENA run accession assigned to the sequencing run.</td></tr>
          <tr><td>rawData_ENA_experiment_accession</td><td>ENA experiment accession (if present).</td></tr>
          <tr><td>rawData_ENA_uploadIssues</td><td>Notes or flags about issues encountered during ENA upload.</td></tr>
          <tr><td>rawData_availableLocally</td><td>Flag indicating raw reads are available locally at the provider.</td></tr>
          <tr><td>rawData_cannotAcquire</td><td>Flag indicating raw reads could not be acquired.</td></tr>
          <tr><td>rawData_COGDAT_uploaded</td><td>Flag showing whether raw reads were uploaded to the COGDAT archive.</td></tr>
          <tr><td>rawData_COGDAT_uploadGivenUp</td><td>Flag if COGDAT upload attempts were abandoned.</td></tr>
          <tr><td>rawData_COGDAT_uploadedTimestamp</td><td>Timestamp of COGDAT raw data upload.</td></tr>
          <tr><td>rawData_COGDAT_ID</td><td>COGDAT identifier for the uploaded raw data.</td></tr>
          <tr><td>rawData_COGDAT_uploadIssues</td><td>Notes or flags about issues encountered during COGDAT upload.</td></tr>
          <tr><td>rawData_reads_removed_potentiallyHuman</td><td>Number of reads removed as potentially human.</td></tr>
          <tr><td>rawData_reads_removed_notAlignedToViralGenome</td><td>Number of reads removed for not aligning to viral genome.</td></tr>
          <tr><td>rawData_reads_notRemoved</td><td>Number of reads retained after filtering.</td></tr>
          <tr><td>rawData_bases_removed_potentiallyHuman</td><td>Number of bases removed as potentially human.</td></tr>
          <tr><td>rawData_bases_removed_notAlignedToViralGenome</td><td>Number of bases removed for not aligning to viral genome.</td></tr>
          <tr><td>rawData_bases_notRemoved</td><td>Number of bases retained after filtering.</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
// Static help page
</script>

<style scoped>
.table-header {
  background-color: var(--num-slate);
  color: #fff;
}

.legend-box {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 1px solid #dee2e6;
  margin-right: 6px;
  vertical-align: middle;
}

.gray-head {
  background-color: #d3d3d3 !important;
  color: #000 !important;
}

.table-bordered th,
.table-bordered td {
  border: 1px solid #dee2e6;
}
.table {
  font-size: 12px;
}

.details-table {
  font-size: 12px;
}
</style>
