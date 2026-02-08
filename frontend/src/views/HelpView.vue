<!-- src/views/HelpView.vue -->
<template>
  <div class="container-fluid">
    <!-- Page Header -->
    <div class="mb-5">
      <h1 class="text-center">Help: Data Format and Upload Instructions</h1>
      <p class="lead">
        This section provides detailed guidelines for uploading single or multiple samples, including the
        required formats for <strong>Sample Metadata</strong>, <strong>Antibiotic Testing Results</strong>,
        and <strong>NGS Data</strong>. Please carefully follow these instructions to ensure successful uploads.
      </p>
    </div>

    <!-- Single Sample Upload -->
    <h2 id="single-upload" class="text-info">Single Sample Upload</h2>
    <p>For single sample uploads, ensure that your files adhere to the following format requirements:</p>

    <h3 id="single-files">Required Files</h3>
    <ul>
      <li>
        <strong>Sample Metadata File:</strong>
        <ul>
          <li>
            A CSV, TSV, or Excel (<code>.xlsx</code>) file containing the sample's identifier, collection details,
            sequencing file names, and other metadata.
          </li>
          <li>
            <strong>File Naming:</strong> You may name your metadata file freely. The FASTQ file names must be listed
            in the appropriate metadata fields (see below).
          </li>
          <li>
            <strong>Format:</strong> The file may use <code>,</code> (comma), <code>;</code> (semicolon), or
            <code>\t</code> (tab) as delimiters — these will be auto-detected. File extensions allowed:
            <code>.csv</code>, <code>.tsv</code>, <code>.txt</code>, <code>.xlsx</code>.
          </li>
          <li>
            <strong>FASTQ File Fields:</strong> You must list the FASTQ file names in one or more of the following fields:
            <ul>
              <li><code>Illumina R1</code> — required if using Illumina platform (paired-end R1 file).</li>
              <li><code>Illumina R2</code> — optional; must be provided only if <code>Illumina R1</code> is provided (paired-end R2 file).</li>
              <li><code>Nanopore</code> — required if using Oxford Nanopore platform.</li>
              <li><code>PacBio</code> — required if using PacBio platform.</li>
            </ul>
            <strong>Important:</strong> FASTQ file names must exactly match the actual uploaded file names (case-sensitive).
          </li>
          <li>Ensure all <strong>mandatory metadata fields</strong> are included.</li>
        </ul>
      </li>

      <li>
        <strong>Antibiotic Testing Information (Optional):</strong>
        <ul>
          <li>
            You may provide antibiotic testing data in <code>one</code> of the following ways:
            <ul>
              <li>
                <strong>Antibiotics File:</strong> A <strong>CSV</strong>, <strong>TSV</strong>, or <strong>Excel (.xlsx)</strong>
                file containing antibiotic testing results.
              </li>
              <li>
                <strong>Antibiotics Info:</strong> A text field in the metadata file summarizing the antibiotic testing information.
              </li>
            </ul>
          </li>
          <li>
            <strong>Important:</strong> You <strong>must not</strong> provide both <code>"Antibiotics File"</code> and
            <code>"Antibiotics Info"</code> at the same time. If an <code>"Antibiotics File"</code> is provided, its filename
            must match exactly what is entered in the <code>"Antibiotics File"</code> field of the metadata file.
          </li>
          <li>
            <strong>Format (For Antibiotics File):</strong> The file may use <code>,</code> (comma), <code>;</code> (semicolon),
            or <code>\t</code> (tab) as delimiters — these will be auto-detected. File extensions allowed:
            <code>.csv</code>, <code>.tsv</code>, <code>.txt</code>, <code>.xlsx</code>.
          </li>
          <li>If an <code>"Antibiotics File"</code> is provided, it must include all mandatory antibiotic testing columns.</li>
        </ul>
      </li>

      <li>
        <strong>NGS Data:</strong>
        <p>There must be at least one of the following files or a combination of two or more of them:</p>
        <ul>
          <li>
            <strong>Illumina:</strong> FASTQ files (<code>.fastq</code>, <code>.fq</code>), either two paired-end files
            (e.g., <code>sample_R1.fastq.gz</code>, <code>sample_R2.fastq.gz</code>) or one single-end file.
          </li>
          <li>
            <strong>Nanopore:</strong> FASTQ files (<code>.fastq</code>, <code>.fq</code>) or unaligned BAM file (<code>.bam</code>).
          </li>
          <li>
            <strong>PacBio:</strong> FASTQ files (<code>.fastq</code>, <code>.fq</code>) or Subreads BAM file (<code>subreads.bam</code>).
          </li>
          <li><strong>Multiple:</strong> A combination of files from the above platforms.</li>
          <li>
            <strong>File Naming:</strong> No specific naming requirements, but a meaningful name is recommended for better tracking
            (e.g., <code>sample_ID_1.fastq.gz</code>, <code>sample_ID_2.fastq.gz</code>, <code>sample_ID.fastq.gz</code>). The
            filename must match exactly as specified in the metadata file fields.
          </li>
        </ul>

        <p class="text-muted mb-0">
          <strong>Note:</strong> Compression is accepted. Supported compressed file formats include <code>.gz</code>, <code>.bz2</code>,
          and <code>.zip</code>. For example: <code>sample.fastq.gz</code>, <code>subreads.bam.bz2</code>.
        </p>
      </li>
    </ul>

    <!-- NGS Files Formatting Guide -->
    <h3 id="ngs-formatting-guide">📌 Example of NGS Files inputs</h3>
    <p>
      The <code>"Illumina R1", "Illumina R2", "Nanopore", and "PacBio"</code> fields in the metadata file must follow a structured
      format to indicate sequencing platforms and their corresponding files.
    </p>

    <div class="table-responsive">
      <table class="table table-bordered">
        <thead class="thead-dark">
          <tr>
            <th>Examples of accepted NGS inputs</th>
            <th>Illumina R1</th>
            <th>Illumina R2</th>
            <th>Nanopore</th>
            <th>PacBio</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Single Platform: <code>Paired-end Illumina</code></td>
            <td>sample_001_R1.fastq.gz</td>
            <td>sample_001_R1.fastq.gz</td>
            <td></td>
            <td></td>
          </tr>
          <tr>
            <td>Single Platform: <code>Single-end Illumina</code></td>
            <td>sample_001_R1.fastq.gz</td>
            <td></td>
            <td></td>
            <td></td>
          </tr>
          <tr>
            <td>Single Platform: <code>Nanopore</code></td>
            <td></td>
            <td></td>
            <td>sample_ont.fastq.gz</td>
            <td></td>
          </tr>
          <tr>
            <td>Single Platform: <code>PacBio</code></td>
            <td></td>
            <td></td>
            <td></td>
            <td></td>
          </tr>
          <tr>
            <td>Multiple Platforms: <code>Paired-end Illumina</code> and <code>Nanopore</code></td>
            <td>sample_001_R1.fastq.gz</td>
            <td>sample_001_R1.fastq.gz</td>
            <td>sample_ont.fastq.gz</td>
            <td></td>
          </tr>
          <tr>
            <td>Multiple Platforms: <code>Paired-end Illumina</code> and <code>PacBio</code></td>
            <td>sample_001_R1.fastq.gz</td>
            <td>sample_001_R1.fastq.gz</td>
            <td></td>
            <td>sample_pacbio.fastq.gz</td>
          </tr>
          <tr>
            <td>Multiple Platforms: <code>Nanopore</code> and <code>PacBio</code></td>
            <td></td>
            <td></td>
            <td>sample_ont.fastq.gz</td>
            <td>sample_pacbio.fastq.gz</td>
          </tr>
          <tr>
            <td>Multiple Platforms: <code>Paired-end Illumina</code>, <code>Nanopore</code> and <code>PacBio</code></td>
            <td>sample_001_R1.fastq.gz</td>
            <td>sample_001_R1.fastq.gz</td>
            <td>sample_ont.fastq.gz</td>
            <td>sample_pacbio.fastq.gz</td>
          </tr>
        </tbody>
      </table>
    </div>

    <h4>🛠 Additional Notes</h4>
    <ul>
      <li>✔ If submitting hybrid sequencing data, you must list all platforms separately.</li>
      <li>✔ File extensions must be correct (e.g., <code>.fastq</code>, <code>.fq</code>, <code>.bam</code>).</li>
      <li>✔ Compressed files are accepted, including <code>.gz</code>, <code>.bz2</code>, and <code>.zip</code> formats.</li>
    </ul>

    <!-- Example of Single Upload Submission -->
    <h3 id="single-examples">Example of Single Upload Submission</h3>
    <div class="table-responsive">
      <table class="table table-striped table-bordered single-ex-table">
        <thead class="table-header">
          <tr>
            <th class="gray-head">Metadata File</th>
            <th class="gray-head">Antibiotic Testing Files</th>
            <th class="gray-head">FASTQ Files</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>sample_001_metadata.csv</td>
            <td>sample_001_antibiotics.csv</td>
            <td>
              sample_001_R1.fastq.gz<br />
              sample_001_R2.fastq.gz
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Bulk Upload Instructions -->
    <h2 id="bulk-upload" class="text-info">Bulk Upload</h2>
    <p>For bulk uploads, the following guidelines must be followed:</p>

    <h3 id="bulk-files">Required Files</h3>
    <ol>
      <li>
        Ensure that all required files are prepared and correctly labeled for each sample:
        <ul>
          <li>One metadata file in CSV format, following the single upload metadata format.</li>
          <li>
            At least one FASTQ file per sample, with filenames matching exactly as listed in the metadata file platform fields.
          </li>
          <li>
            Antibiotic testing data per sample (optional):
            <ul>
              <li>
                <strong>Antibiotics File:</strong> If provided, the filename must match exactly as listed in the
                <code>"Antibiotics File"</code> field of the metadata file.
              </li>
              <li>
                <strong>Antibiotics Info:</strong> If no file is provided, antibiotic testing details can be entered as text in the
                <code>"Antibiotics Info"</code> field of the metadata file.
              </li>
              <li>
                <strong>Important:</strong> You may provide <code>either</code> an <code>"Antibiotics File"</code> <strong>or</strong>
                <code>"Antibiotics Info"</code>, but <strong>not both</strong>.
              </li>
            </ul>
          </li>
        </ul>
      </li>
      <li>
        The metadata file must specify the expected filenames for FASTQ files in the platform fields and, if applicable, for antibiotics
        testing files in the <code>"Antibiotics File"</code> field.
      </li>
      <li>
        Uploaded FASTQ files must match the filenames listed in the metadata file. If an antibiotics file is provided, it must also match the
        filename listed in the metadata file.
      </li>
      <li>
        Upload the metadata file, all FASTQ files, and, if applicable, any antibiotics files directly through the bulk upload form.
      </li>
    </ol>

    <p>Once all files are validated and uploaded, the system will associate them based on sample identifiers and process the submission.</p>

    <h3 id="bulk-examples">Examples of Bulk Submissions</h3>
    <p>The following examples demonstrate how to organize and name your files for a bulk submission:</p>
    <p>Adhering to these examples and guidelines will help ensure your bulk uploads are processed correctly.</p>

    <div class="table-responsive">
      <table class="table table-striped table-bordered bulk-ex-table">
        <thead class="table-header">
          <tr>
            <th class="gray-head">Metadata File</th>
            <th class="gray-head">Antibiotic Testing Files</th>
            <th class="gray-head">FASTQ Files</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>eco_meta_modified.csv</td>
            <td>
              Eco05232_amr.csv<br />
              Eco05239_amr.csv<br />
              Eco05243_amr.csv<br />
              Eco05250_amr.csv<br />
              Eco05274_amr.csv
            </td>
            <td>
              <strong>Eco05232:</strong><br />
              Eco05232-240828_1.fastq.gz<br />
              Eco05232-240828_2.fastq.gz<br />
              <strong>Eco05239:</strong><br />
              Eco05239-240828_1.fastq.gz<br />
              Eco05239-240828_2.fastq.gz<br />
              <strong>Eco05243:</strong><br />
              Eco05243-240828_1.fastq.gz<br />
              Eco05243-240828_2.fastq.gz<br />
              <strong>Eco05250:</strong><br />
              Eco05250-240828_1.fastq.gz<br />
              Eco05250-240828_2.fastq.gz<br />
              <strong>Eco05274:</strong><br />
              Eco05274-240828_1.fastq.gz<br />
              Eco05274-240828_2.fastq.gz
            </td>
          </tr>
          <tr>
            <td>sample_metadata.csv</td>
            <td>
              Sample_001_antibiotics.csv<br />
              Sample_002_antibiotics.csv
            </td>
            <td>
              <strong>Sample_001:</strong><br />
              Sample_001.fastq<br />
              <strong>Sample_002:</strong><br />
              Sample_002.fastq
            </td>
          </tr>
          <tr>
            <td>sample_metadata.csv</td>
            <td>sample_antibiotics.csv</td>
            <td>
              <strong>Sample_001:</strong><br />
              test1.fastq
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Detailed Metadata and Antibiotics Information -->
    <h2 id="details" class="text-info">Detailed Metadata and Antibiotics Information</h2>
    <p>
      This section provides detailed descriptions of the required fields for Sample Metadata and Antibiotic Testing Results.
      The tables below outline the specific fields, their descriptions, expected content, and whether they are mandatory or optional.
      Use this information as a reference when preparing your metadata and antibiotic testing files for upload.
    </p>

    <!-- Legend -->
    <h3 id="sample-meta">Sample Metadata for Single Upload</h3>
    <p>Please follow the format shown below for your metadata.</p>

    <div class="mb-3">
      <p><strong>Legend: Field Requirements</strong></p>
      <div>
        <span class="legend-box mandatory"></span>
        <span>Mandatory Fields</span>
      </div>
      <div>
        <span class="legend-box optional"></span>
        <span>Optional Fields</span>
      </div>
      <div>
        <span class="legend-box groupone"></span>
        <span>At least one required among the group</span>
      </div>
    </div>

    <!-- Metadata Table (static example placeholder) -->
    <div class="table-responsive">
      <table class="table table-striped table-bordered meta-table">
        <thead class="table-header">
          <tr>
            <th colspan="3" class="gray-head">Sample and Isolate Information</th>
            <th colspan="4" class="gray-head">Sample Collection Data</th>
            <th colspan="6" class="gray-head">Sample Collection Facility</th>
            <th colspan="3" class="gray-head">Patient/Host Details</th>
            <th colspan="8" class="gray-head">Sequencing Details</th>
            <th colspan="2" class="gray-head">Antibiotics Details</th>
          </tr>
          <tr>
            <th class="th-mandatory">Sample Identifier</th>
            <th class="th-mandatory">Isolate Species</th>
            <th class="th-optional">Subtype</th>
            <th class="th-mandatory">Collection Date</th>
            <th class="th-optional">Sampling Strategy</th>
            <th class="th-mandatory">Sample Source</th>
            <th class="th-optional">Collection Method</th>
            <th class="th-mandatory">City</th>
            <th class="th-mandatory">Postal Code</th>
            <th class="th-optional">County</th>
            <th class="th-mandatory">State</th>
            <th class="th-mandatory">Country</th>
            <th class="th-optional">Lab Identifier</th>
            <th class="th-optional">Sex</th>
            <th class="th-optional">Age Group</th>
            <th class="th-optional">Country of Putative Exposure</th>
            <th class="th-optional">Sequencing Platform</th>
            <th class="th-mandatory">Sequencing Type</th>
            <th class="th-optional">Library Preparation Kit</th>
            <th class="th-optional">Sequencing Chemistry</th>
            <th class="th-groupone">Illumina R1</th>
            <th class="th-groupone">Illumina R2</th>
            <th class="th-groupone">Nanopore</th>
            <th class="th-groupone">Pacbio</th>
            <th class="th-optional">Antibiotics File</th>
            <th class="th-optional">Antibiotics Info</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Sample_001</td>
            <td>Escherichia coli (NCBI taxid)</td>
            <td>ST131</td>
            <td>01/01/2026</td>
            <td>Surveillance</td>
            <td>Human clinical (hospital)</td>
            <td>Swab</td>
            <td>Tübingen</td>
            <td>72076</td>
            <td>Tübingen</td>
            <td>Baden-Württemberg</td>
            <td>Germany</td>
            <td>LAB-123</td>
            <td>Male</td>
            <td>Adult</td>
            <td>Germany</td>
            <td>Illumina</td>
            <td>Whole genome sequencing</td>
            <td>Nextera XT</td>
            <td>V2.5</td>
            <td>sample_001_R1.fastq.gz</td>
            <td>sample_001_R2.fastq.gz</td>
            <td></td>
            <td></td>
            <td>sample_001_antibiotics.csv</td>
            <td></td>
          </tr>
        </tbody>
      </table>
    </div>

    <a href="/download_sample_csv/" class="btn btn-secondary">Download Sample CSV</a>

    <br /><br />

    <!-- Antibiotic Testing Results for Single Upload -->
    <h3 id="sample_anti">Antibiotic Testing Results for Single Upload</h3>
    <p>Please follow the format shown below for your antibiotics testing data.</p>

    <div class="table-responsive">
      <table class="table table-striped table-bordered anti-table">
        <thead class="table-header">
          <tr>
            <th class="th-optional">Testing Method</th>
            <th class="th-mandatory">Tested Antibiotic</th>
            <th class="th-mandatory">Observed Antibiotic Resistance SIR</th>
            <th class="th-optional">Observed Antibiotic Resistance MIC (mg/L)</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Disk diffusion</td>
            <td>Ampicillin</td>
            <td>R</td>
            <td>&gt;=4.0</td>
          </tr>
        </tbody>
      </table>
    </div>

    <a href="/download_antibiotics_csv/" class="btn btn-secondary">Download Antibiotics Testing CSV</a>

    <br /><br />

    <!-- Detailed Metadata Fields -->
    <h3 id="detailed-meta">Detailed Metadata Fields</h3>
    <p class="lead">
      This table outlines the required and optional metadata fields for sample uploads, as well as their descriptions and conditions.
    </p>

    <div class="table-responsive">
      <table class="table table-striped table-bordered details-table">
        <thead class="thead-dark">
          <tr>
            <th>Field</th>
            <th>Description</th>
            <th>Content</th>
            <th>Condition</th>
          </tr>
        </thead>
        <tbody>
          <tr class="table-primary">
            <td colspan="4"><strong>Sample and Isolate Information</strong></td>
          </tr>
          <tr>
            <td>Sample Identifier</td>
            <td>Unique ID for tracking the sample.</td>
            <td>Unique ID</td>
            <td class="cell-mandatory">Mandatory</td>
          </tr>
          <tr>
            <td>Isolate Species</td>
            <td>NCBI Taxonomy ID.</td>
            <td>NCBI taxonomy ID</td>
            <td class="cell-mandatory">Mandatory</td>
          </tr>
          <tr>
            <td>Subtype</td>
            <td>Sequence type, strain, serotype, etc.</td>
            <td>Text</td>
            <td class="cell-optional">Optional</td>
          </tr>

          <tr class="table-primary">
            <td colspan="4"><strong>Sample Collection Data</strong></td>
          </tr>
          <tr>
            <td>Collection Date</td>
            <td>When the sample was collected.</td>
            <td>Day/Month/Year</td>
            <td class="cell-mandatory">Mandatory</td>
          </tr>
          <tr>
            <td>Sampling Strategy</td>
            <td>Reason for sampling.</td>
            <td>Surveillance, suspected outbreak, sequencing for diagnostic purposes, other [Text]</td>
            <td class="cell-optional">Optional</td>
          </tr>
          <tr>
            <td>Sample Source</td>
            <td>Type of sample source.</td>
            <td>Human clinical (hospital), human screening (hospital), medical devices, etc.</td>
            <td class="cell-mandatory">Mandatory</td>
          </tr>
          <tr>
            <td>Collection Method</td>
            <td>Method used to collect the sample.</td>
            <td>Text</td>
            <td class="cell-optional">Optional</td>
          </tr>

          <tr class="table-primary">
            <td colspan="4"><strong>Antibiotics Details</strong></td>
          </tr>
          <tr>
            <td>Antibiotics File</td>
            <td>
              A CSV or TSV file containing antibiotic testing results for the sample. The filename must match exactly as specified in the metadata.
            </td>
            <td><code>Sample_antibiotics.csv</code> [CSV, TSV]</td>
            <td class="cell-optional">Optional</td>
          </tr>
          <tr>
            <td>Antibiotics Info</td>
            <td>Text-based antibiotic resistance information, provided directly in the metadata instead of a separate file.</td>
            <td><code>Resistant to ampicillin and tetracycline</code> [Text]</td>
            <td class="cell-optional">Optional</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Detailed Antibiotic Testing Results Fields -->
    <h3 id="detailed-anti">Detailed Antibiotic Testing Results Fields</h3>
    <p>
      This section provides detailed descriptions of the required fields for Antibiotic Testing Results.
      The table below outlines the specific fields, their descriptions, expected content, and whether they are mandatory or optional.
    </p>

    <p class="lead">Antibiotic resistance data can be included using one of two methods:</p>
    <ul>
      <li><strong>Antibiotics File:</strong> A structured CSV or TSV file containing antibiotic susceptibility test results for each sample.</li>
      <li>
        <strong>Antibiotics Info:</strong> A free-text field within the metadata file that provides antibiotic resistance details.
        <ul>
          <li>
            <strong>Example Entries:</strong>
            <ul>
              <li><code>"Resistant to beta-lactams"</code></li>
              <li><code>"Multidrug-resistant strain"</code></li>
              <li><code>"SIR results pending, MIC tested at 2 mg/L for Ciprofloxacin"</code></li>
            </ul>
          </li>
        </ul>
      </li>
    </ul>

    <p><strong>Important:</strong> Only one method should be used per sample. Do not provide both an <code>Antibiotics File</code> and <code>Antibiotics Info</code> for the same sample.</p>

    <div class="table-responsive">
      <table class="table table-striped table-bordered details-anti-table">
        <thead class="thead-dark">
          <tr>
            <th>Field</th>
            <th>Description</th>
            <th>Accepted Content</th>
            <th>Condition</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Testing Method</td>
            <td>Method used to determine resistance.</td>
            <td>e.g., Disk diffusion, Vitek</td>
            <td class="cell-optional">Optional</td>
          </tr>
          <tr>
            <td>Tested Antibiotic</td>
            <td>Name of the antibiotic tested.</td>
            <td>e.g., Ampicillin, Ciprofloxacin</td>
            <td class="cell-mandatory">Mandatory</td>
          </tr>
          <tr>
            <td>Observed Antibiotic Resistance SIR</td>
            <td>Resistance classification based on guidelines.</td>
            <td>Susceptible (S), Intermediate (I), Resistant (R)</td>
            <td class="cell-mandatory">Mandatory</td>
          </tr>
          <tr>
            <td>Observed Antibiotic Resistance MIC (mg/L)</td>
            <td>Minimum Inhibitory Concentration (quantitative).</td>
            <td>e.g., 0.5, &gt;=4.0</td>
            <td class="cell-optional">Optional</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Resubmission -->
    <h2 id="resubmission" class="text-info">Resubmission of Metadata Files</h2>

    <p>
      If your metadata file was accepted with <strong>warnings</strong>, you will be allowed to resubmit a corrected version of that file.
    </p>

    <p>
      The system will notify you immediately after upload if resubmission is allowed. You can also check the
      <RouterLink to="/dashboard">Dashboard</RouterLink>
      at any time to view the current status of your submissions.
    </p>

    <ul>
      <li>
        Only <strong>metadata files</strong> can be resubmitted. If accepted with warnings, a <strong>Resubmit Metadata</strong>
        option will be shown in the dashboard.
      </li>
      <li>
        To resubmit, upload your corrected file using the provided resubmission link. The system will validate it and update the
        submission accordingly.
      </li>
      <li>
        Once your file passes validation <strong>without warnings</strong>, resubmission will no longer be required and the resubmit
        button will disappear.
      </li>
      <li>
        ⚠️ If your submission includes warnings for <strong>antibiotics</strong> or <strong>FASTQ</strong> files, those will also be
        shown in the dashboard, but <strong>they cannot be resubmitted</strong>.
      </li>
      <li>If you wish to correct antibiotics or FASTQ data, you must create a new submission.</li>
      <li>The Submission ID is displayed after upload — you can use it to track and manage resubmissions later.</li>
    </ul>

    <p class="mb-0">
      For a full overview of your submissions, including file statuses, warnings, and resubmission options, visit your
      <RouterLink to="/dashboard">Dashboard</RouterLink>.
    </p>
  </div>
</template>

<script setup>
// Static help page (no API calls required)
</script>

<style scoped>
.table-header {
  background-color: #003366;
  color: #fff;
}

/* Legend */
.legend-box {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 1px solid #dee2e6;
  margin-right: 6px;
  vertical-align: middle;
}
.legend-box.mandatory {
  background-color: #ffd1d1;
}
.legend-box.optional {
  background-color: #ffffe0;
}
.legend-box.groupone {
  background-color: #ffe5b4;
}

/* Header colors matching the template */
.gray-head {
  background-color: #d3d3d3 !important;
  color: #000 !important;
}

.th-mandatory {
  background-color: #ffd1d1 !important;
  color: #000 !important;
}
.th-optional {
  background-color: #ffffe0 !important;
  color: #000 !important;
}
.th-groupone {
  background-color: #ffe5b4 !important;
  color: #000 !important;
}

.cell-mandatory {
  background-color: #ffd1d1 !important;
}
.cell-optional {
  background-color: #ffffe0 !important;
}

/* Table borders + font */
.table-bordered th,
.table-bordered td {
  border: 1px solid #dee2e6;
}
.table {
  font-size: 12px;
}

.single-ex-table,
.bulk-ex-table,
.meta-table,
.anti-table,
.details-table,
.details-anti-table {
  font-size: 12px;
}
</style>
