<template>
  <div class="container-fluid">
    <!-- Page Header -->
    <div class="mb-5">
      <h1 class="text-center">Help: NUM-SAR Data Format and Upload Instructions</h1>
      <p class="lead">
        This section provides detailed guidelines for uploading single or multiple samples, including the
        required formats for <strong>Sample Metadata</strong> and <strong>NGS Data</strong>. Please carefully follow
        these instructions to ensure successful uploads.
      </p>
    </div>

    <div class="alert alert-warning">
      <strong>⚠️ Uploading large sequencing files (multiple GB)?</strong>
      Please use <strong>Google Chrome, Microsoft Edge, or Safari</strong> rather than Firefox.
      Firefox has known issues completing very large uploads on some networks — especially
      corporate/institute networks with antivirus or web-filtering software — where the upload
      can stall partway through and never finish. Chromium-based browsers and Safari do not show
      this problem.
    </div>

    <!-- Single Sample Upload -->
    <h2 id="single-upload" class="text-primary">Single Sample Upload</h2>
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
        <thead class="table-header">
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
            <td>sample_001_R2.fastq.gz</td>
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
            <td>sample_pacbio.fastq.gz</td>
          </tr>
          <tr>
            <td>Multiple Platforms: <code>Paired-end Illumina</code> and <code>Nanopore</code></td>
            <td>sample_001_R1.fastq.gz</td>
            <td>sample_001_R2.fastq.gz</td>
            <td>sample_ont.fastq.gz</td>
            <td></td>
          </tr>
          <tr>
            <td>Multiple Platforms: <code>Paired-end Illumina</code> and <code>PacBio</code></td>
            <td>sample_001_R1.fastq.gz</td>
            <td>sample_001_R2.fastq.gz</td>
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
            <td>sample_001_R2.fastq.gz</td>
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
            <th class="gray-head">FASTQ Files</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>sample_001_metadata.csv</td>
            <td>
              sample_001_R1.fastq.gz<br />
              sample_001_R2.fastq.gz
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Bulk Upload Instructions -->
    <h2 id="bulk-upload" class="text-primary">Bulk Upload</h2>
    <p>For bulk uploads, the following guidelines must be followed:</p>

    <h3 id="bulk-files">Required Files</h3>
    <ol>
      <li>
        Ensure that all required files are prepared and correctly labeled for each sample:
        <ul>
          <li>One metadata file in CSV format, following the single upload metadata format.</li>
          <li>
            At least one FASTQ file per sample, with filenames matching exactly as listed in the metadata file's
            platform fields (<code>Illumina R1</code> / <code>Illumina R2</code> / <code>Nanopore</code> / <code>PacBio</code>).
          </li>
        </ul>
      </li>
      <li>
        The metadata file must specify the expected filenames for FASTQ files in the platform fields
        (<code>Illumina R1</code> / <code>Illumina R2</code> / <code>Nanopore</code> / <code>PacBio</code>).
      </li>
      <li>
        Uploaded FASTQ files must match the filenames listed in the metadata file.
      </li>
      <li>
        Upload the metadata file and all FASTQ files directly through the bulk upload form.
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
            <th class="gray-head">FASTQ Files</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>eco_meta_modified.csv</td>
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
              <strong>Sample_001:</strong><br />
              Sample_001.fastq<br />
              <strong>Sample_002:</strong><br />
              Sample_002.fastq
            </td>
          </tr>
          <tr>
            <td>sample_metadata.csv</td>
            <td>
              <strong>Sample_001:</strong><br />
              test1.fastq
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Detailed Metadata Information -->
    <h2 id="details" class="text-primary">Detailed Metadata Information</h2>
    <p>
      This section provides detailed descriptions of the required fields for Sample Metadata.
      The table below outlines the specific fields, their descriptions, expected content, and whether they are mandatory or optional.
      Use this information as a reference when preparing your metadata file for upload.
    </p>

    <!-- Legend -->
    <h3 id="sample-meta">Sample Metadata for Single Upload</h3>
    <p>
      Please use the detailed metadata fields table below for the sample metadata format.
    </p>

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
        <span>At least one required (sequencing file fields)</span>
      </div>
      <div>
        <strong>✓</strong>
        <span> under "Research Only" = used internally only, not sent to RKI/DEMIS</span>
      </div>
    </div>

    <a href="/static/num-sar_metadata.csv" class="btn btn-secondary">Download Sample CSV</a>

    <br /><br />

    <!-- Detailed Metadata Fields -->
    <h3 id="detailed-meta">Detailed Metadata Fields</h3>
    <p class="lead">
      This table outlines the required and optional metadata fields for sample uploads, as well as their descriptions and conditions.
      Fields marked <strong>Research Only</strong> are used internally and are not converted into the RKI/DEMIS output file.
    </p>

    <div class="table-responsive">
      <table class="table table-striped table-bordered details-table">
        <thead class="table-header">
          <tr>
            <th>Field</th>
            <th>Description</th>
            <th>Content</th>
            <th>Condition</th>
            <th>Research Only</th>
          </tr>
        </thead>
        <tbody>
          <tr class="table-primary">
            <td colspan="5"><strong>Sample and Isolate Information</strong></td>
          </tr>
          <tr>
            <td>LAB_SEQUENCE_ID</td>
            <td>Unique ID for tracking the sample (called "Sample identifier" in Gensurv). Not user-generated — it is the ID assigned during sample sequencing by the submitting Sequencing Lab. Used for communication in case of internal queries.</td>
            <td>Text</td>
            <td class="cell-mandatory">Mandatory</td>
            <td></td>
          </tr>
          <tr>
            <td>SPECIES</td>
            <td>Isolate or organism species name (called "Isolate Species" in Gensurv). Use official NCBI Taxonomy or ENA conventions; no other accepted. Example: Norovirus norwalkense (ENA) or Norwalk virus (NCBI).</td>
            <td>Text</td>
            <td class="cell-mandatory">Mandatory</td>
            <td></td>
          </tr>
          <tr>
            <td>ISOLATE</td>
            <td>Identification or description of the specific individual micro-organism from which this sequence was obtained, to separate replicates. Examples: Isolate 1, Hu-GII.4-Berlin-2026-DE, NV-2026-Outbreak-09A, Replicate 3.</td>
            <td>Text</td>
            <td class="cell-optional">Optional</td>
            <td></td>
          </tr>
          <tr>
            <td>SUBTYPE</td>
            <td>Final classification assigned to the virus sample (e.g., Sequence type, strain, serotype, etc.). Examples: GII.4; GII.P16_GII.4.</td>
            <td>Text</td>
            <td class="cell-optional">Optional</td>
            <td>✓</td>
          </tr>
          <tr>
            <td>Typing_Strategy</td>
            <td>The method, target genomic region, or bioinformatic tool used to identify the pathogen subtype. Examples: Polymerase region, Capsid region, Dual-typing, Nextclade, BLAST, phylogenetic analyses, kmer clustering.</td>
            <td>Text</td>
            <td class="cell-optional">Optional</td>
            <td>✓</td>
          </tr>

          <tr class="table-primary">
            <td colspan="5"><strong>Sample Collection Data</strong></td>
          </tr>
          <tr>
            <td>DATE_OF_SAMPLING</td>
            <td>The date of sample collection from the patient or source. Example: 2026-11-25.</td>
            <td>YYYY-MM-DD or DAY/MONTH/YEAR</td>
            <td class="cell-optional">Optional</td>
            <td></td>
          </tr>
          <tr>
            <td>ISOLATION SOURCE</td>
            <td>Describes the local source of the organism from which the sequence was obtained, whether from a patient or the environment. Example: Upper respiratory swab specimen.</td>
            <td>Stool/faeces, Anal/rectal swab, Vomitus, Inanimate surroundings, Water, Food, Other [Text]</td>
            <td class="cell-mandatory">Mandatory</td>
            <td></td>
          </tr>
          <tr>
            <td>Storage Duration</td>
            <td>Time between sampling and sequencing of the sample.</td>
            <td>&lt; 1 week, 1 week - 1 month, 1–6 months, 6-12 months, &gt; 12 months</td>
            <td class="cell-optional">Optional</td>
            <td>✓</td>
          </tr>
          <tr>
            <td>County</td>
            <td>County (Landkreis/Stadtkreis) of sample origin.</td>
            <td>Text</td>
            <td class="cell-optional">Optional</td>
            <td>✓</td>
          </tr>
          <tr>
            <td>Country</td>
            <td>Country where the sample was collected.</td>
            <td>Text</td>
            <td class="cell-mandatory">Mandatory</td>
            <td>✓</td>
          </tr>

          <tr class="table-primary">
            <td colspan="5"><strong>Sample Collection Facility</strong></td>
          </tr>
          <tr>
            <td>DATE_OF_RECEIVING</td>
            <td>The date when the sample arrived at the laboratory.</td>
            <td>YYYY-MM-DD</td>
            <td class="cell-mandatory">Mandatory</td>
            <td></td>
          </tr>
          <tr>
            <td>PRIME_DIAGNOSTIC_LAB.NAME</td>
            <td>Name of the primary diagnostic laboratory collecting the sample. Example: Labor Dr. Limbach &amp; Kollegen GbR.</td>
            <td>Text</td>
            <td class="cell-mandatory">Mandatory</td>
            <td></td>
          </tr>
          <tr>
            <td>PRIME_DIAGNOSTIC_LAB.EMAIL</td>
            <td>E-mail of the prime diagnostic lab.</td>
            <td>Text</td>
            <td class="cell-mandatory">Mandatory</td>
            <td></td>
          </tr>
          <tr>
            <td>PRIME_DIAGNOSTIC_LAB.ADDRESS</td>
            <td>Street of the prime diagnostic lab.</td>
            <td>Text</td>
            <td class="cell-mandatory">Mandatory</td>
            <td></td>
          </tr>
          <tr>
            <td>PRIME_DIAGNOSTIC_LAB.CITY</td>
            <td>City of the main diagnostic laboratory.</td>
            <td>Text</td>
            <td class="cell-mandatory">Mandatory</td>
            <td></td>
          </tr>
          <tr>
            <td>PRIME_DIAGNOSTIC_LAB.POSTAL_CODE</td>
            <td>Postal code of the primary diagnostic laboratory.</td>
            <td>Text</td>
            <td class="cell-mandatory">Mandatory</td>
            <td></td>
          </tr>
          <tr>
            <td>PRIME_DIAGNOSTIC_LAB.COUNTRY</td>
            <td>Country of the primary diagnostic laboratory.</td>
            <td>Text</td>
            <td class="cell-mandatory">Mandatory</td>
            <td></td>
          </tr>
          <tr>
            <td>PRIME_DIAGNOSTIC_LAB.FEDERAL_STATE</td>
            <td>Federal state or region of the primary diagnostic laboratory.</td>
            <td>Text</td>
            <td class="cell-optional">Optional</td>
            <td></td>
          </tr>

          <tr class="table-primary">
            <td colspan="5"><strong>Patient/Host Details</strong></td>
          </tr>
          <tr>
            <td>HOST_SEX</td>
            <td>Sex of the patient from whom the sample was collected.</td>
            <td>Male, Female, Diverse, Unknown</td>
            <td class="cell-optional">Optional</td>
            <td></td>
          </tr>
          <tr>
            <td>HOST_BIRTH_MONTH</td>
            <td>The birth month of the patient.</td>
            <td></td>
            <td class="cell-optional">Optional</td>
            <td></td>
          </tr>
          <tr>
            <td>HOST_BIRTH_YEAR</td>
            <td>The birth year of the patient.</td>
            <td></td>
            <td class="cell-optional">Optional</td>
            <td></td>
          </tr>
          <tr>
            <td>Age Group</td>
            <td>Age group of the patient, for cases where the user does not have the exact birth month and year.</td>
            <td>0-4, 5-14, 15-34, 35-59, 60-79, 80+, Unknown</td>
            <td class="cell-optional">Optional</td>
            <td>✓</td>
          </tr>
          <tr>
            <td>GEOGRAPHIC_LOCATION</td>
            <td>Three-digit postal code of the patient's place of residence. Leading zeros are retained. Example: 123.</td>
            <td>3 digit number</td>
            <td class="cell-optional">Optional</td>
            <td></td>
          </tr>
          <tr>
            <td>Patient Status</td>
            <td>Admission status of the host.</td>
            <td>Outpatient, Inpatient, Unknown</td>
            <td class="cell-optional">Optional</td>
            <td>✓</td>
          </tr>
          <tr>
            <td>Non patient sample</td>
            <td>Rare, but sample can come from non-human sources, such as from a food-related outbreak in case of a suspected point source. Leave blank if sample is from human.</td>
            <td>Text</td>
            <td class="cell-optional">Optional</td>
            <td>✓</td>
          </tr>
          <tr>
            <td>Suspected outbreak</td>
            <td>Binary (Yes/No).</td>
            <td>Yes, No</td>
            <td class="cell-optional">Optional</td>
            <td>✓</td>
          </tr>

          <tr class="table-primary">
            <td colspan="5"><strong>Sequencing Details</strong></td>
          </tr>
          <tr>
            <td>SEQUENCING_REASON</td>
            <td>The epidemiological reason or strategy for selecting and sequencing the sample.</td>
            <td>Surveillance, Outbreak, Targeted study, Diagnostic confirmation, Other [Text]</td>
            <td class="cell-mandatory">Mandatory</td>
            <td></td>
          </tr>
          <tr>
            <td>DATE_OF_SEQUENCING</td>
            <td>The date the sample was sequenced.</td>
            <td>YYYY-MM-DD</td>
            <td class="cell-mandatory">Mandatory</td>
            <td></td>
          </tr>
          <tr>
            <td>SEQUENCING_LAB.NAME</td>
            <td>Full official name of the facility performing the sequencing.</td>
            <td>Text</td>
            <td class="cell-mandatory">Mandatory</td>
            <td></td>
          </tr>
          <tr>
            <td>SEQUENCING_LAB.EMAIL</td>
            <td>Contact email address for the sequencing laboratory.</td>
            <td>Email address</td>
            <td class="cell-mandatory">Mandatory</td>
            <td></td>
          </tr>
          <tr>
            <td>SEQUENCING_LAB.ADDRESS</td>
            <td>Street address and house number of the sequencing laboratory.</td>
            <td>Text</td>
            <td class="cell-mandatory">Mandatory</td>
            <td></td>
          </tr>
          <tr>
            <td>SEQUENCING_LAB.CITY</td>
            <td>City where the sequencing laboratory is located.</td>
            <td>Text</td>
            <td class="cell-mandatory">Mandatory</td>
            <td></td>
          </tr>
          <tr>
            <td>SEQUENCING_LAB.POSTAL_CODE</td>
            <td>Postal/ZIP code of the sequencing laboratory.</td>
            <td>Text</td>
            <td class="cell-mandatory">Mandatory</td>
            <td></td>
          </tr>
          <tr>
            <td>SEQUENCING_LAB.COUNTRY</td>
            <td>Country where the sequencing laboratory is located.</td>
            <td>Text</td>
            <td class="cell-mandatory">Mandatory</td>
            <td></td>
          </tr>
          <tr>
            <td>SEQUENCING_STRATEGY</td>
            <td>The experimental sequencing strategy used to process the sample, based on the ENA library strategy vocabulary.</td>
            <td>WGS, AMPLICON, METAGENOMIC, RNA-Seq, or OTHER [Text]</td>
            <td class="cell-mandatory">Mandatory</td>
            <td></td>
          </tr>
          <tr>
            <td>SEQUENCING_PLATFORM</td>
            <td>Sequencing platform used to generate read files.</td>
            <td>Illumina, Oxford Nanopore, PacBio, Ion Torrent, Other [Text]</td>
            <td class="cell-mandatory">Mandatory</td>
            <td></td>
          </tr>
          <tr>
            <td>SEQUENCING_INSTRUMENT</td>
            <td>Specific model of instrument used for sequencing.</td>
            <td>Illumina MiSeq, Illumina NextSeq, Oxford Nanopore GridION, Oxford Nanopore MinION, PacBio Sequel II, Other [Text]</td>
            <td class="cell-mandatory">Mandatory</td>
            <td></td>
          </tr>
          <tr>
            <td>Library Preparation Kit</td>
            <td>Kit used for preparing the sequencing library. Examples: Nextera XT, TruSeq DNA, SMRTbell, and others.</td>
            <td>Text</td>
            <td class="cell-optional">Optional</td>
            <td>✓</td>
          </tr>
          <tr>
            <td>ADAPTER</td>
            <td>The specific molecular adapter sequences or index names added to the DNA/RNA fragments during library prep. Example: TAGCGAGT.</td>
            <td>Text</td>
            <td class="cell-optional">Optional</td>
            <td></td>
          </tr>
          <tr>
            <td>NAME_AMP_PROTOCOL</td>
            <td>Name of the specific protocol used to amplify the target pathogen genomic regions. Example: CVD_Artic_Protokoll_2.1, ARTICv4.1.</td>
            <td>Text</td>
            <td class="cell-optional">Optional</td>
            <td></td>
          </tr>
          <tr>
            <td>PRIMER_SCHEME</td>
            <td>The specific primer design panel used to amplify the pathogen DNA/RNA. Example: ARTICv4.1.</td>
            <td>Text</td>
            <td class="cell-optional">Optional</td>
            <td></td>
          </tr>
          <tr>
            <td>REPOSITORY_NAME</td>
            <td>The name of the external database where this genetic sequence has already been or is planned to be uploaded. If submitted to multiple databases, list them separated by a semicolon. Example: GISAID, ENA.</td>
            <td>Text</td>
            <td class="cell-mandatory">Mandatory</td>
            <td></td>
          </tr>
          <tr>
            <td>REPOSITORY_LINK</td>
            <td>Hyperlink to the sample in the REPOSITORY_NAME repository.</td>
            <td>Text</td>
            <td class="cell-optional">Optional</td>
            <td></td>
          </tr>
          <tr>
            <td>REPOSITORY_ID</td>
            <td>The ID of the sample in the repository.</td>
            <td>Text</td>
            <td class="cell-optional">Optional</td>
            <td></td>
          </tr>
          <tr>
            <td>UPLOAD_DATE</td>
            <td>The date the sample was uploaded to the repository.</td>
            <td>Date</td>
            <td class="cell-optional">Optional</td>
            <td></td>
          </tr>
          <tr>
            <td>Illumina R1</td>
            <td>Filename of the Illumina paired-end R1 FASTQ file.</td>
            <td>sample_001_R1.fastq.gz</td>
            <td class="cell-groupone">At least one required</td>
            <td></td>
          </tr>
          <tr>
            <td>Illumina R2</td>
            <td>Filename of the Illumina paired-end R2 FASTQ file. Only allowed if Illumina R1 exists.</td>
            <td>sample_001_R2.fastq.gz</td>
            <td class="cell-groupone">At least one required</td>
            <td></td>
          </tr>
          <tr>
            <td>Nanopore</td>
            <td>Filename of the Oxford Nanopore sequencing file.</td>
            <td>sample_ont.fastq.gz</td>
            <td class="cell-groupone">At least one required</td>
            <td></td>
          </tr>
          <tr>
            <td>PacBio</td>
            <td>Filename of the PacBio sequencing file.</td>
            <td>sample_pacbio.fastq.gz</td>
            <td class="cell-groupone">At least one required</td>
            <td></td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- RKI Metadata Fields -->
    <h2 id="rki-fields" class="text-primary">RKI Metadata Fields (Downloadable File)</h2>
    <p>
      The fields below are the ones included in the RKI/DEMIS metadata file generated from your submission. Most are
      derived directly from the fields you provide above; a few are generated automatically by the system. For full
      field definitions, see the
      <a href="https://wiki.gematik.de/spaces/DSKB/pages/659360260/Metadaten+f%C3%BCr+Upload+via+csv+oder+LIS-Schnittstelle" target="_blank" rel="noopener">
        official RKI/DEMIS documentation
      </a>.
    </p>

    <div class="table-responsive">
      <table class="table table-striped table-bordered details-table">
        <thead class="table-header">
          <tr>
            <th>RKI Field</th>
            <th>Condition</th>
          </tr>
        </thead>
        <tbody>
          <tr class="table-primary">
            <td colspan="2"><strong>Sample and Isolate Information</strong></td>
          </tr>
          <tr><td>STATUS</td><td class="cell-mandatory">Mandatory</td></tr>
          <tr><td>LAB_SEQUENCE_ID</td><td class="cell-mandatory">Mandatory</td></tr>
          <tr><td>MELDETATBESTAND</td><td class="cell-mandatory">Mandatory</td></tr>
          <tr><td>SPECIES</td><td class="cell-mandatory">Mandatory</td></tr>
          <tr><td>SPECIES_CODE</td><td class="cell-mandatory">Mandatory</td></tr>
          <tr><td>ISOLATE</td><td class="cell-optional">Optional</td></tr>

          <tr class="table-primary">
            <td colspan="2"><strong>Sample Collection Data</strong></td>
          </tr>
          <tr><td>DATE_OF_SAMPLING</td><td class="cell-optional">Optional</td></tr>
          <tr><td>ISOLATION SOURCE</td><td class="cell-mandatory">Mandatory</td></tr>
          <tr><td>ISOLATION SOURCE_CODE / SAMPLE_TYPE</td><td class="cell-mandatory">Mandatory</td></tr>

          <tr class="table-primary">
            <td colspan="2"><strong>Sample Collection Facility</strong></td>
          </tr>
          <tr><td>DATE_OF_RECEIVING</td><td class="cell-mandatory">Mandatory</td></tr>
          <tr><td>PRIME_DIAGNOSTIC_LAB.NAME</td><td class="cell-mandatory">Mandatory</td></tr>
          <tr><td>PRIME_DIAGNOSTIC_LAB.EMAIL</td><td class="cell-mandatory">Mandatory</td></tr>
          <tr><td>PRIME_DIAGNOSTIC_LAB.ADDRESS</td><td class="cell-mandatory">Mandatory</td></tr>
          <tr><td>PRIME_DIAGNOSTIC_LAB.CITY</td><td class="cell-mandatory">Mandatory</td></tr>
          <tr><td>PRIME_DIAGNOSTIC_LAB.POSTAL_CODE</td><td class="cell-mandatory">Mandatory</td></tr>
          <tr><td>PRIME_DIAGNOSTIC_LAB.COUNTRY</td><td class="cell-mandatory">Mandatory</td></tr>
          <tr><td>PRIME_DIAGNOSTIC_LAB.FEDERAL_STATE</td><td class="cell-optional">Optional</td></tr>

          <tr class="table-primary">
            <td colspan="2"><strong>Patient/Host Details</strong></td>
          </tr>
          <tr><td>HOST_SEX</td><td class="cell-optional">Optional</td></tr>
          <tr><td>HOST_BIRTH_MONTH</td><td class="cell-optional">Optional</td></tr>
          <tr><td>HOST_BIRTH_YEAR</td><td class="cell-optional">Optional</td></tr>
          <tr><td>GEOGRAPHIC_LOCATION</td><td class="cell-optional">Optional</td></tr>

          <tr class="table-primary">
            <td colspan="2"><strong>Sequencing Details</strong></td>
          </tr>
          <tr><td>SEQUENCING_LAB.DEMIS_LAB_ID</td><td class="cell-mandatory">Mandatory</td></tr>
          <tr><td>SEQUENCING_LAB.NAME</td><td class="cell-mandatory">Mandatory</td></tr>
          <tr><td>SEQUENCING_LAB.EMAIL</td><td class="cell-mandatory">Mandatory</td></tr>
          <tr><td>SEQUENCING_LAB.ADDRESS</td><td class="cell-mandatory">Mandatory</td></tr>
          <tr><td>SEQUENCING_LAB.CITY</td><td class="cell-mandatory">Mandatory</td></tr>
          <tr><td>SEQUENCING_LAB.POSTAL_CODE</td><td class="cell-mandatory">Mandatory</td></tr>
          <tr><td>SEQUENCING_LAB.COUNTRY</td><td class="cell-mandatory">Mandatory</td></tr>
          <tr><td>DATE_OF_SEQUENCING</td><td class="cell-mandatory">Mandatory</td></tr>
          <tr><td>SEQUENCING_REASON</td><td class="cell-mandatory">Mandatory</td></tr>
          <tr><td>SEQUENCING_PLATFORM</td><td class="cell-mandatory">Mandatory</td></tr>
          <tr><td>SEQUENCING_INSTRUMENT</td><td class="cell-mandatory">Mandatory</td></tr>
          <tr><td>SEQUENCING_STRATEGY</td><td class="cell-mandatory">Mandatory</td></tr>
          <tr><td>NAME_AMP_PROTOCOL</td><td class="cell-optional">Optional</td></tr>
          <tr><td>ADAPTER</td><td class="cell-optional">Optional</td></tr>
          <tr><td>PRIMER_SCHEME</td><td class="cell-optional">Optional</td></tr>
          <tr><td>UPLOAD_STATUS</td><td class="cell-mandatory">Mandatory</td></tr>
          <tr><td>REPOSITORY_NAME</td><td class="cell-mandatory">Mandatory</td></tr>
          <tr><td>REPOSITORY_LINK</td><td class="cell-optional">Optional</td></tr>
          <tr><td>REPOSITORY_ID</td><td class="cell-optional">Optional</td></tr>
          <tr><td>UPLOAD_DATE</td><td class="cell-optional">Optional</td></tr>
          <tr><td>FILE_1_NAME</td><td class="cell-mandatory">Mandatory</td></tr>
          <tr><td>FILE_1_SHA256SUM</td><td class="cell-mandatory">Mandatory</td></tr>
          <tr><td>FILE_2_NAME</td><td class="cell-optional">Optional</td></tr>
          <tr><td>FILE_2_SHA256SUM</td><td class="cell-optional">Optional</td></tr>
        </tbody>
      </table>
    </div>


    <!-- Resubmission -->
    <h2 id="resubmission" class="text-primary">Resubmission of Metadata Files</h2>

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
        If your submission includes warnings for <strong>FASTQ</strong> files, those will also be shown in the dashboard,
        but <strong>they cannot be resubmitted</strong>.
      </li>
      <li>If you wish to correct FASTQ data, you must create a new submission.</li>
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
.table-header th {
  background-color: var(--num-slate);
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
  background-color: var(--num-slate) !important;
  color: #fff !important;
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
.cell-groupone {
  background-color: #ffe5b4 !important;
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
.details-table {
  font-size: 12px;
}
</style>
