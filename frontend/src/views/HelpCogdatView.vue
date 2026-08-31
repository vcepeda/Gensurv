<template>
  <div class="container-fluid">
    <!-- Page Header -->
    <div class="mb-5">
      <h1 class="text-center">Help: CoGDat Metadata Columns</h1>
      <p class="lead">
        Part of the sequence and metadata held here was collected through
        <a href="https://cogdat.de/" target="_blank" rel="noopener">CoGDat</a>, the SARS-CoV-2 Genomics
        Data Platform. This page describes the columns that come with those records, so you can
        interpret the values you see in search results and exports.
      </p>
    </div>

    <!-- About CoGDat -->
    <h2 id="about" class="text-info">About CoGDat</h2>
    <p>
      CoGDat is a research initiative that collects, stores and analyses SARS-CoV-2 sequence data produced
      in Germany. It gathers raw sequencing data (FASTQ files) directly from sequencing laboratories doing
      molecular surveillance, alongside the genome assemblies reported to the Robert Koch Institute, and
      publishes what it can in the European Nucleotide Archive (ENA). It is coordinated at the University
      of Tübingen as a joint initiative within the Netzwerk Universitätsmedizin (NUM) and DeCOI.
    </p>
    <p>
      Because records pass through several submission routes — RKI, GISAID, ENA and the CoGDat archive
      itself — most columns below record the status, timestamp and identifier of one of those routes.
      Technical documentation for the CoGDat metadata schema is available at
      <a href="https://docs.cogdat.de" target="_blank" rel="noopener">docs.cogdat.de</a>.
    </p>

    <!-- How to read the table -->
    <h2 id="reading" class="text-info">How to Read This Table</h2>
    <ul>
      <li>Columns marked as a flag hold <code>1</code> for yes and <code>0</code> or an empty value for no.</li>
      <li>Timestamp columns record when a step happened; an empty timestamp means the step has not run.</li>
      <li>
        Accession columns (ENA, GISAID, RKI) are only filled once the corresponding submission has
        succeeded, so an empty accession alongside a "given up" flag means the submission was abandoned.
      </li>
    </ul>

    <!-- Column Reference -->
    <h2 id="columns" class="text-info">Column Reference</h2>
    <p class="lead">
      This table lists every column in the CoGDat metadata export, grouped by what it describes.
    </p>

    <div class="table-responsive">
      <table class="table table-striped table-bordered details-table">
        <thead class="thead-dark">
          <tr>
            <th>Column</th>
            <th>Description</th>
            <th>Content</th>
          </tr>
        </thead>
        <tbody>
          <tr class="table-primary">
            <td colspan="3"><strong>Sample Identification</strong></td>
          </tr>
          <tr>
            <td>sampleID</td>
            <td>Internal sample identifier used in CoGDat exports.</td>
            <td>Text</td>
          </tr>
          <tr>
            <td>plateID</td>
            <td>Laboratory plate or batch identifier.</td>
            <td>Text</td>
          </tr>
          <tr>
            <td>HHU_id</td>
            <td>Local laboratory identifier for the sample (HHU).</td>
            <td>Text</td>
          </tr>
          <tr>
            <td>pseudonym_prefix</td>
            <td>Prefix used when pseudonymising sample IDs.</td>
            <td>Text</td>
          </tr>
          <tr>
            <td>pseudonym_numerical</td>
            <td>Numeric part of the pseudonymised identifier.</td>
            <td>Number</td>
          </tr>

          <tr class="table-primary">
            <td colspan="3"><strong>Sequence and Quality</strong></td>
          </tr>
          <tr>
            <td>sequenceupdated</td>
            <td>Timestamp when the sequence data was last updated.</td>
            <td>Timestamp</td>
          </tr>
          <tr>
            <td>Ns</td>
            <td>Number of ambiguous bases (N) in the consensus sequence. Lower is better.</td>
            <td>Number</td>
          </tr>
          <tr>
            <td>pangolin</td>
            <td>Pangolin lineage assigned to the sequence at the time of analysis.</td>
            <td>Text. Example: BA.5.2</td>
          </tr>
          <tr>
            <td>pangolin_recent</td>
            <td>
              Most recent Pangolin lineage. Lineage definitions change over time, so this can differ from
              the original <code>pangolin</code> value for the same sequence.
            </td>
            <td>Text</td>
          </tr>
          <tr>
            <td>finalized</td>
            <td>Whether the sequence is finalized.</td>
            <td>Flag (1 = yes)</td>
          </tr>

          <tr class="table-primary">
            <td colspan="3"><strong>Processing Status and Timestamps</strong></td>
          </tr>
          <tr>
            <td>runsstatus</td>
            <td>Status of the sequencing run.</td>
            <td>Text. Example: Finished</td>
          </tr>
          <tr>
            <td>processingstatus</td>
            <td>Processing workflow status for the sample.</td>
            <td>Text</td>
          </tr>
          <tr>
            <td>lastpushed</td>
            <td>Timestamp when the record was last pushed to downstream systems.</td>
            <td>Timestamp</td>
          </tr>
          <tr>
            <td>sequenceAnalysisTimestamp</td>
            <td>When the sequence analysis pipeline ran.</td>
            <td>Timestamp</td>
          </tr>
          <tr>
            <td>addedToTableTimestamp</td>
            <td>When the record was added to the CoGDat table.</td>
            <td>Timestamp</td>
          </tr>
          <tr>
            <td>firstSequenceTimestamp</td>
            <td>Timestamp for the first available sequence for this sample.</td>
            <td>Timestamp</td>
          </tr>
          <tr>
            <td>firstSequenceFewer3000NsTimestamp</td>
            <td>
              Timestamp of the first sequence for this sample with fewer than 3000 ambiguous bases, i.e.
              the first sequence meeting the quality threshold.
            </td>
            <td>Timestamp</td>
          </tr>
          <tr>
            <td>arrivalAtVirologyDate</td>
            <td>Date the sample arrived at the virology lab.</td>
            <td>Date</td>
          </tr>

          <tr class="table-primary">
            <td colspan="3"><strong>GISAID Submission</strong></td>
          </tr>
          <tr>
            <td>GISAIDuploaded</td>
            <td>Whether the sequence was uploaded to GISAID.</td>
            <td>Flag (1 = yes)</td>
          </tr>
          <tr>
            <td>GISAIDuploadedtimestamp</td>
            <td>Timestamp of the GISAID upload.</td>
            <td>Timestamp</td>
          </tr>
          <tr>
            <td>GISAIDISL</td>
            <td>GISAID ISL accession assigned to the sequence, if any.</td>
            <td>Text. Example: EPI_ISL_402124</td>
          </tr>
          <tr>
            <td>GISAIDupload_givenUp</td>
            <td>Whether upload attempts to GISAID were abandoned.</td>
            <td>Flag (1 = yes)</td>
          </tr>

          <tr class="table-primary">
            <td colspan="3"><strong>RKI Submission</strong></td>
          </tr>
          <tr>
            <td>RKIUploadAttempted</td>
            <td>Whether an upload to the Robert Koch Institute was attempted.</td>
            <td>Flag (1 = yes)</td>
          </tr>
          <tr>
            <td>RKIRejected</td>
            <td>Whether the RKI rejected the submission.</td>
            <td>Flag (1 = yes)</td>
          </tr>
          <tr>
            <td>RKIUploadedTimestamp</td>
            <td>Timestamp of the RKI upload, if applicable.</td>
            <td>Timestamp</td>
          </tr>
          <tr>
            <td>RKIIMSID</td>
            <td>
              RKI IMS identifier (Integrierte Molekulare Surveillance) associated with the upload.
            </td>
            <td>Text</td>
          </tr>

          <tr class="table-primary">
            <td colspan="3"><strong>ENA Raw Data Submission</strong></td>
          </tr>
          <tr>
            <td>rawData_ENA_uploaded</td>
            <td>Whether the raw reads were uploaded to the European Nucleotide Archive.</td>
            <td>Flag (1 = yes)</td>
          </tr>
          <tr>
            <td>rawData_ENA_uploadGivenUp</td>
            <td>Whether ENA upload attempts were abandoned.</td>
            <td>Flag (1 = yes)</td>
          </tr>
          <tr>
            <td>rawData_ENA_uploadTimestamp</td>
            <td>Timestamp of the ENA raw data upload.</td>
            <td>Timestamp</td>
          </tr>
          <tr>
            <td>rawData_ENA_sample_accession</td>
            <td>ENA sample accession, if uploaded.</td>
            <td>Text. Example: ERS1234567</td>
          </tr>
          <tr>
            <td>rawData_ENA_run_accession</td>
            <td>ENA run accession assigned to the sequencing run.</td>
            <td>Text. Example: ERR1234567</td>
          </tr>
          <tr>
            <td>rawData_ENA_experiment_accession</td>
            <td>ENA experiment accession, if present.</td>
            <td>Text. Example: ERX1234567</td>
          </tr>
          <tr>
            <td>rawData_ENA_uploadIssues</td>
            <td>Notes or flags about issues encountered during the ENA upload.</td>
            <td>Text</td>
          </tr>

          <tr class="table-primary">
            <td colspan="3"><strong>Raw Data Availability</strong></td>
          </tr>
          <tr>
            <td>rawData_availableLocally</td>
            <td>Whether the raw reads are available locally at the providing laboratory.</td>
            <td>Flag (1 = yes)</td>
          </tr>
          <tr>
            <td>rawData_cannotAcquire</td>
            <td>Whether the raw reads could not be acquired.</td>
            <td>Flag (1 = yes)</td>
          </tr>

          <tr class="table-primary">
            <td colspan="3"><strong>CoGDat Raw Data Archive</strong></td>
          </tr>
          <tr>
            <td>rawData_COGDAT_uploaded</td>
            <td>Whether the raw reads were uploaded to the CoGDat archive.</td>
            <td>Flag (1 = yes)</td>
          </tr>
          <tr>
            <td>rawData_COGDAT_uploadGivenUp</td>
            <td>Whether CoGDat upload attempts were abandoned.</td>
            <td>Flag (1 = yes)</td>
          </tr>
          <tr>
            <td>rawData_COGDAT_uploadedTimestamp</td>
            <td>Timestamp of the CoGDat raw data upload.</td>
            <td>Timestamp</td>
          </tr>
          <tr>
            <td>rawData_COGDAT_ID</td>
            <td>CoGDat identifier for the uploaded raw data.</td>
            <td>Text</td>
          </tr>
          <tr>
            <td>rawData_COGDAT_uploadIssues</td>
            <td>Notes or flags about issues encountered during the CoGDat upload.</td>
            <td>Text</td>
          </tr>

          <tr class="table-primary">
            <td colspan="3"><strong>Read Filtering</strong></td>
          </tr>
          <tr>
            <td>rawData_reads_removed_potentiallyHuman</td>
            <td>Number of reads removed because they were potentially of human origin.</td>
            <td>Number</td>
          </tr>
          <tr>
            <td>rawData_reads_removed_notAlignedToViralGenome</td>
            <td>Number of reads removed because they did not align to the viral genome.</td>
            <td>Number</td>
          </tr>
          <tr>
            <td>rawData_reads_notRemoved</td>
            <td>Number of reads retained after filtering.</td>
            <td>Number</td>
          </tr>
          <tr>
            <td>rawData_bases_removed_potentiallyHuman</td>
            <td>Number of bases removed as potentially human.</td>
            <td>Number</td>
          </tr>
          <tr>
            <td>rawData_bases_removed_notAlignedToViralGenome</td>
            <td>Number of bases removed for not aligning to the viral genome.</td>
            <td>Number</td>
          </tr>
          <tr>
            <td>rawData_bases_notRemoved</td>
            <td>Number of bases retained after filtering.</td>
            <td>Number</td>
          </tr>
        </tbody>
      </table>
    </div>

    <p class="mb-0">
      To browse the records that carry these columns, go to your
      <RouterLink to="/dashboard">Dashboard</RouterLink>.
    </p>
  </div>
</template>

<script setup>
// Static help page (no API calls required)
</script>

<style scoped>
.table-header {
  background-color: var(--num-slate);
  color: #fff;
}

.gray-head {
  background-color: #d3d3d3 !important;
  color: #000 !important;
}

/* Table borders + font */
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