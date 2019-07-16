import logging
import os

from agr.vcf_file_generator import VcfFileGenerator
from agr.orthology_file_generator import OrthologyFileGenerator
from agr.daf_file_generator import DafFileGenerator
import agr.assembly_sequence as agr_asm_seq
from agr.data_source import DataSource


host = os.environ.get('NEO4J_HOST', 'localhost')

port = int(os.environ.get('NEO4J_PORT', 7687))

alliance_db_version = os.environ.get('ALLIANCE_DATABASE_VERSION', 'test')

uri = "bolt://" + host + ":" + str(port)
assembly_to_s3_uri = {
    'R6.27': 'https://s3.amazonaws.com/agrjbrowse/FlyBase/fruitfly/fasta/',
    'GRCz11': 'https://s3.amazonaws.com/agrjbrowse/zfin/zebrafish/fasta/',
    'WBcel235': 'https://s3.amazonaws.com/agrjbrowse/WormBase/c_elegans_PRJNA13758/fasta/',
    'Rnor_6.0': 'https://s3.amazonaws.com/agrjbrowse/RGD/rat/fasta/',
    'GRCm38': 'https://s3.amazonaws.com/agrjbrowse/MGI/mouse/fasta/'
}


def setup_logging(logger_name):
    logging.basicConfig(level=logging.DEBUG)


def main(generated_files_folder='generated_files',
         fasta_sequences_folder='sequences',
         skip_chromosomes={'Unmapped_Scaffold_8_D1580_D1567'}):
    #generate_vcf_files(generated_files_folder, fasta_sequences_folder, skip_chromosomes)
    #generate_orthology_file(generated_files_folder, alliance_db_version)
    generate_daf_file(generated_files_folder, alliance_db_version)
    exit()


def generate_vcf_files(generated_files_folder, fasta_sequences_folder, skip_chromosomes):
    os.makedirs(generated_files_folder, exist_ok=True)
    os.makedirs(fasta_sequences_folder, exist_ok=True)
    variants_query = """MATCH (s:Species)-[:FROM_SPECIES]-(a:Allele)-[:VARIATION]-(v:Variant)-[l:LOCATED_ON]-(c:Chromosome)
MATCH (v:Variant)-[:VARIATION_TYPE]-(st:SOTerm)
OPTIONAL MATCH (a:Allele)-[:IS_ALLELE_OF]-(g:Gene)
RETURN c.primaryKey AS chromosome,
       v.globalId AS globalId,
       v.genomicReferenceSequence AS genomicReferenceSequence,
       v.genomicVariantSequence AS genomicVariantSequence,
       v.hgvs_nomenclature AS hgvsNomenclature,
       v.dataProvider AS dataProvider,
       a.symbol AS symbol,
       collect(g.primaryKey) as alleleOfGenes,
       l.start AS start,
       l.end AS end,
       l.assembly AS assembly,
       s.name AS species,
       st.nameKey AS soTerm
    """
    data_source = DataSource(uri, variants_query)
    agr_asm_seq.ensure_downloaded(fasta_sequences_folder, assembly_to_s3_uri)
    gvf = VcfFileGenerator(data_source,
                           generated_files_folder,
                           fasta_sequences_folder,
                           alliance_db_version)
    gvf.generate_files(skip_chromosomes=skip_chromosomes)


def generate_orthology_file(generated_files_folder, alliance_db_version):
    orthology_query = """MATCH (species1)<-[sa:FROM_SPECIES]-(gene1:Gene)-[o:ORTHOLOGOUS]->(gene2:Gene)-[sa2:FROM_SPECIES]->(species2:Species)
WHERE o.strictFilter
OPTIONAL MATCH (algorithm:OrthoAlgorithm)-[m:MATCHED]-(ogj:OrthologyGeneJoin)-[association:ASSOCIATION]-(gene1)
WHERE ogj.primaryKey = o.primaryKey
OPTIONAL MATCH (algorithm2:OrthoAlgorithm)-[m2:NOT_MATCHED]-(ogj2:OrthologyGeneJoin)-[ASSOCIATION]-(gene1)
WHERE ogj2.primaryKey = o.primaryKey
RETURN gene1.primaryKey AS gene1ID,
       gene1.symbol AS gene1Symbol,
       gene2.primaryKey AS gene2ID,
       gene2.symbol AS gene2Symbol,
       collect(DISTINCT algorithm.name) as Algorithms,
       count(DISTINCT algorithm.name) AS numAlgorithmMatch,
       count(DISTINCT algorithm2.name) AS numAlgorithmNotMatched,
       toString(o.isBestScore) AS best,
       toString(o.isBestRevScore) AS bestRev,
       species1.primaryKey AS species1TaxonID,
       species1.name AS species1Name,
       species2.primaryKey AS species2TaxonID,
       species2.name AS species2Name"""
    data_source = DataSource(uri, orthology_query)
    of = OrthologyFileGenerator(data_source, 
                                generated_files_folder,
                                alliance_db_version)
    of.generate_file()


def generate_daf_file(generated_files_folder, alliance_db_version):
    daf_query = """MATCH (dej:Association:DiseaseEntityJoin)-[:ASSOCIATION]-(object)-[da:IS_MARKER_FOR|:IS_IMPLICATED_IN|:IMPLICATED_VIA_ORTHOLOGY|:BIOMARKER_VIA_ORTHOLOGY]->(disease:DOTerm)
WHERE (object:Gene OR object:Allele)
    AND da.uuid = dej.primaryKey
MATCH (object)-[FROM_SPECIES]->(species:Species)
OPTIONAL MATCH (ec:Ontology:ECOTerm)-[:ASSOCIATION]-(:PublicationEvidenceCodeJoin)-[:EVIDENCE]-(dej:Association:DiseaseEntityJoin)
OPTIONAL MATCH (p:Publication)-[:ASSOCIATION]-(:PublicationEvidenceCodeJoin)-[:EVIDENCE]-(dej:Association:DiseaseEntityJoin)
OPTIONAL MATCH (object)-[o:ORTHOLOGOUS]-(oGene:Gene)
WHERE o.strictFilter AND (ec.primaryKey = "ECO:0000250" OR ec.primaryKey = "ECO:0000266") // ISS and ISO respectively
OPTIONAL MATCH (object)-[IS_ALLELE_OF]->(gene:Gene)
RETURN  object.taxonId AS taxonId,
        species.name AS speciesName,
        collect(DISTINCT oGene.primaryKey) AS withOrthologs,
        labels(object) AS objectType,
        object.primaryKey AS dbObjectID,
        object.symbol AS dbObjectSymbol,
        p.pubMedId AS pubMedID,
        p.pubModId As pubModID,
        type(da) AS associationType,
        collect(DISTINCT gene.primaryKey) AS inferredGeneAssociation,
        disease.doId AS DOID,
        disease.name as DOname,
        ec.primaryKey AS evidenceCode,
        dej.dateAssigned AS dateAssigned,
        da.dataProvider AS dataProvider"""
    data_source = DataSource(uri, daf_query)
    daf = DafFileGenerator(data_source,
                           generated_files_folder,
                           alliance_db_version)
    daf.generate_file() 


if __name__ == '__main__':
    main()
