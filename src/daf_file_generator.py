import sys

import logging
from dateutil.parser import parse
from datetime import datetime
from time import gmtime, strftime

logger = logging.getLogger(name=__name__)


class DafFileGenerator:

    file_header_template = """#########################################################################
#
# Disease Association Format (DAF)
# Source: Alliance of Genome Resources (Alliance)
# Orthology Filter: Stringent
# Datebase Version: {databaseVersion}
# Date: {datetimeNow}
#
#########################################################################
"""

    def __init__(self, disease_associations, generated_files_folder, database_version):
        self.disease_associations = disease_associations
        self.database_version = database_version
        self.generated_files_folder = generated_files_folder

    @classmethod
    def _generate_header(cls, database_version):
        return cls.file_header_template.format(datetimeNow=strftime("%Y-%m-%d %H:%M:%S", gmtime()),
                databaseVersion=database_version)

    def generate_file(self):
        output_filepath = self.generated_files_folder + "/agr-daf-" + self.database_version + ".tsv"
        disease_file = open(output_filepath,'w')
        disease_file.write(self._generate_header(self.database_version))
    
        columns = ["Taxon",
                   "SpeciesName",
                   "DBobjectType",
                   "DBObjectID",
                   "DBObjectSymbol",
                   #"InferredGeneAssociation",
                   #"GeneProductFormID",
                   #"AdditionalGeneticComponent",
                   #"ExperimentalConditions",
                   "AssociationType",
                   #"Qualifier",
                   "DOID",
                   "DOname",
                   "withOrthologs",
                   #"Modifier-AssociationType",
                   #"Modifier-Qualifier",
                   #"Modifier-Genetic",
                   #"Modifier-ExperimentalConditions",
                   "EvidenceCode",
                   #"genetic-sex",
                   "Reference",
                   "Date",
                   "Source"]

        tsv_writer = csv.DictWriter(expression_file, delimiter='\t', fieldnames=columns)
        tsv_writer.writeheader()

        for disease_association in self.disease_associations:
            db_object_type = "allele" if disease_association["objectType"][0] == "Feature" else disease_association["objectType"][0].lower()
            pub_id = disease_association["pubMedID"] if disease_association["pubMedID"] else disease_association["pubModID"]
            if pub_id is None:
                pub_id = ""
 
            with_orthologs = "|".join(set(disease_association["withOrthologs"])) if disease_association["withOrthologs"] else ""
            do_name = disease_association["DOname"] if disease_association["DOname"] else ""
            inferred_gene_association = ""
            if db_object_type == "gene":
                inferred_gene_association = disease_association["dbObjectID"]
            elif db_object_type == "allele":
                inferred_gene_association = ",".join(disease_association["inferredGeneAssociation"])

            if disease_association["evidenceCode"] is not None:
                evidence_code = disease_association["evidenceCode"]
            else:
                evidence_code = ""
            gene_product_form_id = ""
            additional_genetic_component = ""
            experimental_conditions = ""
            qualifier = ""
            modifier_association_type = ""
            modifier_qualifier = ""
            modifier_genetic = ""
            modifier_experimental_conditions = ""
            genetic_sex = ""
            if disease_association["dateAssigned"] is None and disease_association["associationType"] in ["IMPLICATED_VIA_ORTHOLOGY",
                                                                                                          "BIOMARKER_VIA_ORTHOLOGY"]:
                date_str = strftime("%Y-%m-%d %H:%M:%S", gmtime())
            else:
                date_str = disease_association["dateAssigned"]

            row = dict(zip(columns, [disease_association["taxonId"],
                                     disease_association["speciesName"],
                                     db_object_type,
                                     disease_association["dbObjectID"],
                                     disease_association["dbObjectSymbol"],
                                     #inferred_gene_association,
                                     #gene_product_form_id,
                                     #additional_genetic_component,
                                     #experimental_conditions,
                                     disease_association["associationType"].lower(),
                                     #qualifier,
                                     disease_association["DOID"],
                                     do_name,
                                     with_orthologs,
                                     #modifier_association_type,
                                     #modifier_qualifier,
                                     #modifier_genetic,
                                     #modifier_experimental_conditions,
                                     evidence_code,
                                     #genetic_sex,
                                     pub_id,
                                     datetime.strptime(date_str[:10], "%Y-%m-%d").strftime("%Y%m%d"),
                                     disease_association["dataProvider"])
            writer.writerows(row)
        disease_file.close()