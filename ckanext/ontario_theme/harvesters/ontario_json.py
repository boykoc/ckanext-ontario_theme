import json
import logging
import requests
from hashlib import sha1
import traceback
import uuid

from ckan import model
from ckan import logic
from ckan import plugins as p
from ckanext.harvest.model import HarvestObject, HarvestObjectExtra

from ckanext.dcat import converters
from ckanext.ontario_theme import converters as ontario_converters


from ckanext.dcat.harvesters.base import DCATHarvester

log = logging.getLogger(__name__)

blacklist = [
    "https://geohub.lio.gov.on.ca/datasets/874e7fa67ce94cc5b1e8e98c59ca06eb_17",
    "https://geohub.lio.gov.on.ca/datasets/b83d0aef05fa49da9e12288bdb36992b_16",
    "https://geohub.lio.gov.on.ca/datasets/07ee3e454ce64271b49247d27b366920_33",
    "https://geohub.lio.gov.on.ca/datasets/7eed650db8dc4973bb65338c3b8dddb1_32",
    "https://geohub.lio.gov.on.ca/datasets/68853b605c844c6ebe041003b4c71b56_26",
    "https://geohub.lio.gov.on.ca/datasets/d7f97a8758894bf48993ee2c2d477b6a",
    "https://geohub.lio.gov.on.ca/datasets/0d640cfa721149169a0766273b73b5df",
    "https://geohub.lio.gov.on.ca/datasets/cfd2c039e0f0447fa051e5ee5b3f96ce",
    "https://geohub.lio.gov.on.ca/datasets/6a1fb58c285046939295372883782856_18",
    "https://geohub.lio.gov.on.ca/datasets/9356556635ca4b0ab92376202c6b899e_19",
    "https://geohub.lio.gov.on.ca/datasets/a22d6994220e486db81ba564413e54bf",
    "https://geohub.lio.gov.on.ca/datasets/63fcfaa0914b4e9389e2835fc5fc990c",
    "https://geohub.lio.gov.on.ca/datasets/4a83d157a2c24b4b9f32266d997e3632_23",
    "https://geohub.lio.gov.on.ca/datasets/4e27c9fcc492483c9012d443b26ec346",
    "https://geohub.lio.gov.on.ca/datasets/2d7925bc21754eae92cae9bd68b91531",
    "https://geohub.lio.gov.on.ca/datasets/4ee94762ab4e453f95fd977bfbf59e4a",
    "https://geohub.lio.gov.on.ca/datasets/fc220beef25d47ef91b390b52db183dd",
    "https://geohub.lio.gov.on.ca/datasets/bb33adeb800e4a6f9cbeb9488ed6ff47",
    "https://geohub.lio.gov.on.ca/datasets/d334a6822306406496fc46247903c0b0",
    "https://geohub.lio.gov.on.ca/datasets/05e11a3eb7494e1aacf34a38905a37c7",
    "https://geohub.lio.gov.on.ca/datasets/b1c5673c187e4a23a1f489068a1fb6dd",
    "https://geohub.lio.gov.on.ca/datasets/0b85652fc2614214804aa926764bae1a",
    "https://geohub.lio.gov.on.ca/datasets/dbf3c6d432b34076bcd36b904bafedd3",
    "https://geohub.lio.gov.on.ca/datasets/da3cab4e0d5c44319141a00fe05f9142",
    "https://geohub.lio.gov.on.ca/datasets/5b639418e0844745bdd10fed3eabe8dc",
    "https://geohub.lio.gov.on.ca/datasets/b277c8f786ba450683d8453cb7d4ae5b",
    "https://geohub.lio.gov.on.ca/datasets/881f283adce5471fa12c464bd876f222",
    "https://geohub.lio.gov.on.ca/datasets/8972af640eb24f42b9a99616f69d8fd4",
    "https://geohub.lio.gov.on.ca/datasets/56d95c5e3254491a87ab43dde8c82e29",
    "https://geohub.lio.gov.on.ca/datasets/90e1d11778c9451ea7a60663252a684c",
    "https://geohub.lio.gov.on.ca/datasets/a82a502e21ca4bd390f1e12b3d9f7c69",
    "https://geohub.lio.gov.on.ca/datasets/27fc653f66e74452873dafc0b7655171",
    "https://geohub.lio.gov.on.ca/datasets/165de3ea58fb4cbdb1ac8575ded000d4_39",
    "https://geohub.lio.gov.on.ca/datasets/8f066c0289fe49a2938bbf2a4208b2fe_37",
    "https://geohub.lio.gov.on.ca/datasets/96516cf38756446d976fc996f9210036_36",
    "https://geohub.lio.gov.on.ca/datasets/3c17da38a83f41e88facaec7b9d48360_35",
    "https://geohub.lio.gov.on.ca/datasets/1affe762e956487f8158b87f89434440_34",
    "https://geohub.lio.gov.on.ca/datasets/6e60708204ef4ea5870422a2bbed99f7",
    "https://geohub.lio.gov.on.ca/datasets/08ce425de40b47508552133e29bdf695",
    "https://geohub.lio.gov.on.ca/datasets/64fb702e16204c3e88b528d9759f1174_14",
    "https://geohub.lio.gov.on.ca/datasets/11be9127e6ae43c4850793a3a2ee943c_13",
    "https://geohub.lio.gov.on.ca/datasets/d0656e0ec1284a0db0593eb2d04b4578",
    "https://geohub.lio.gov.on.ca/datasets/e92db937280d4b57bc0a8b0ad912ff6f",
    "https://geohub.lio.gov.on.ca/datasets/9862a351316343a491f0830a51751856",
    "https://geohub.lio.gov.on.ca/datasets/3649ef49222e4f6890b38c1a867da887",
    "https://geohub.lio.gov.on.ca/datasets/66e1d7fff92740a69ea2d9241d5e7c47",
    "https://geohub.lio.gov.on.ca/datasets/5c7234afb69845bba528203016a9d4d3",
    "https://geohub.lio.gov.on.ca/datasets/601abb68588c4a258c23a12c911f18f9",
    "https://geohub.lio.gov.on.ca/datasets/e33d18ed2a7d435ebee948c9e08022ae",
    "https://geohub.lio.gov.on.ca/datasets/9ff6a35dea43406f8b0c4b269b3d93a7",
    "https://geohub.lio.gov.on.ca/datasets/a9d3c2f21f824e9eba071124ec053875",
    "https://geohub.lio.gov.on.ca/datasets/9b043f7475f3462d846469b2c66e2e87_12",
    "https://geohub.lio.gov.on.ca/datasets/9de0dad6f1b3435eb46df8ee49f4ecfd",
    "https://geohub.lio.gov.on.ca/datasets/f5161b64430e49ff9b2839d2c4ac6299_0",
    "https://geohub.lio.gov.on.ca/datasets/c936574a192346a1a416efaaa62119f8",
    "https://geohub.lio.gov.on.ca/datasets/0d7e26b1b48142a8a44dc4175615e538",
    "https://geohub.lio.gov.on.ca/datasets/3af9d132e00840e3b3bcdf04beaa1778",
    "https://geohub.lio.gov.on.ca/datasets/6eb8f15364be4c128b5c73402e0de82e",
    "https://geohub.lio.gov.on.ca/datasets/06021cf20bdb460c9092d3e79709ce0e",
    "https://geohub.lio.gov.on.ca/datasets/3b7b68205baa4e138eb4e29671876b22",
    "https://geohub.lio.gov.on.ca/datasets/b5bee6164e8a4490beb01d2423feab13",
    "https://geohub.lio.gov.on.ca/datasets/fc0bb25784544c16bb5fb1384c7ceb1a",
    "https://geohub.lio.gov.on.ca/datasets/8bbd4c5d1e214465b58b016d602de979",
    "https://geohub.lio.gov.on.ca/datasets/5872f3b8cb9541aa915762833246795e",
    "https://geohub.lio.gov.on.ca/datasets/e2417e9c460c488987f81485ac5169e8",
    "https://geohub.lio.gov.on.ca/datasets/1e75654c85134e5da8bae36de212867a"
]

class OntarioJSONHarvester(DCATHarvester):

    def geohub_identifier_from_url(self, identifier_url):
        '''Returns a string id with the layer index if it exists.
        '''
        identifier = identifier_url.split('/')[-1] # keep layer index.
        return identifier

    def hubtype_table(self, identifier_url):
        '''Returns boolean.
        If hubtype_table returns true, skip the record.
        hubtype: "table" ignore it.  These are "sub-sets" of existing datasets.
        relations will be in the description for now anyway. 
        This value is only available through the geohub api and requires its own call.
        '''
        is_table = False

        identifier = self.geohub_identifier_from_url(identifier_url)
        geohub_endpoint = "https://geohub.lio.gov.on.ca/api/v3/datasets/{}".format(identifier)
        geohub_response = requests.get(geohub_endpoint)
        hubType = geohub_response.json()["data"]["attributes"]["hubType"]

        if hubType == "Table":
            is_table = True

        return is_table

    def info(self):
        return {
            'name': 'ontario_json',
            'title': 'Ontario Geohub',
            'description': 'Harvester for DCAT dataset descriptions ' +
                           'serialized as JSON into Ontario schema'
        }


    def _get_guids_and_datasets(self, content):

        doc = json.loads(content)

        if isinstance(doc, list):
            # Assume a list of datasets
            datasets = doc
        elif isinstance(doc, dict):
            datasets = doc.get('dataset', [])
        else:
            raise ValueError('Wrong JSON object')

        for dataset in datasets:

            as_string = json.dumps(dataset)

            # Get identifier
            guid = dataset.get('identifier')

            if not guid:
                # This is bad, any ideas welcomed
                guid = sha1(as_string).hexdigest()

            if guid not in blacklist and not self.hubtype_table(guid):
                yield guid, as_string

    def fetch_stage(self, harvest_object):
        return True

    def _get_package_dict(self, harvest_object):

        content = harvest_object.content

        dcat_dict = json.loads(content)

        package_dict = ontario_converters.dcat_to_ontario(dcat_dict)

        return package_dict, dcat_dict


    def gather_stage(self, harvest_job):
        log.debug('In DCATJSONHarvester gather_stage')

        ids = []

        # Get the previous guids for this source
        query = \
            model.Session.query(HarvestObject.guid, HarvestObject.package_id) \
            .filter(HarvestObject.current == True) \
            .filter(HarvestObject.harvest_source_id == harvest_job.source.id)
        guid_to_package_id = {}

        for guid, package_id in query:
            guid_to_package_id[guid] = package_id

        guids_in_db = list(guid_to_package_id.keys())

        guids_in_source = []

        # Get file contents
        url = harvest_job.source.url

        previous_guids = []
        page = 1
        while True:

            try:
                content, content_type = \
                    self._get_content_and_type(url, harvest_job, page)
            except requests.exceptions.HTTPError as error:
                if error.response.status_code == 404:
                    if page > 1:
                        # Server returned a 404 after the first page, no more
                        # records
                        log.debug('404 after first page, no more pages')
                        break
                    else:
                        # Proper 404
                        msg = 'Could not get content. Server responded with ' \
                            '404 Not Found'
                        self._save_gather_error(msg, harvest_job)
                        return None
                else:
                    # This should never happen. Raising just in case.
                    raise

            if not content:
                return None

            try:

                batch_guids = []
                for guid, as_string in self._get_guids_and_datasets(content):

                    log.debug('Got identifier: {0}'
                              .format(guid.encode('utf8')))
                    batch_guids.append(guid)

                    if guid not in previous_guids:

                        if guid in guids_in_db:
                            # actually, does dataset need to be updated?


                            # Dataset needs to be updated
                            obj = HarvestObject(
                                guid=guid, job=harvest_job,
                                package_id=guid_to_package_id[guid],
                                content=as_string,
                                extras=[HarvestObjectExtra(key='status',
                                                           value='change')])
                        else:
                            # Dataset needs to be created
                            obj = HarvestObject(
                                guid=guid, job=harvest_job,
                                content=as_string,
                                extras=[HarvestObjectExtra(key='status',
                                                           value='new')])
                        obj.save()
                        ids.append(obj.id)

                if len(batch_guids) > 0:
                    guids_in_source.extend(set(batch_guids)
                                           - set(previous_guids))
                else:
                    log.debug('Empty document, no more records')
                    # Empty document, no more ids
                    break

            except ValueError as e:
                msg = 'Error parsing file: {0}'.format(str(e))
                self._save_gather_error(msg, harvest_job)
                return None

            if sorted(previous_guids) == sorted(batch_guids):
                # Server does not support pagination or no more pages
                log.debug('Same content, no more pages')
                break

            page = page + 1

            previous_guids = batch_guids

        # Check datasets that need to be deleted
        guids_to_delete = set(guids_in_db) - set(guids_in_source)
        for guid in guids_to_delete:
            obj = HarvestObject(
                guid=guid, job=harvest_job,
                package_id=guid_to_package_id[guid],
                extras=[HarvestObjectExtra(key='status', value='delete')])
            ids.append(obj.id)
            model.Session.query(HarvestObject).\
                filter_by(guid=guid).\
                update({'current': False}, False)
            obj.save()

        return ids


    def import_stage(self, harvest_object):
        log.debug('In DCATJSONHarvester import_stage')
        if not harvest_object:
            log.error('No harvest object received')
            return False

        if self.force_import:
            status = 'change'
        else:
            status = self._get_object_extra(harvest_object, 'status')

        if status == 'delete':
            # Don't delete package quite yet. we'll have to manually delete it later
            context = {'model': model, 'session': model.Session,
                       'user': self._get_user_name()}

            p.toolkit.get_action('package_delete')(
                context, {'id': harvest_object.package_id})
            log.info('Deleted package {0} with guid {1}'
                     .format(harvest_object.package_id, harvest_object.guid))

            # what we need here is something to notify opendata@ontario.ca that we're deleting 
            return True

        if harvest_object.content is None:
            self._save_object_error(
                'Empty content for object %s' % harvest_object.id,
                harvest_object, 'Import')
            return False

        # Get the last harvested object (if any)
        previous_object = model.Session.query(HarvestObject) \
            .filter(HarvestObject.guid == harvest_object.guid) \
            .filter(HarvestObject.current == True) \
            .first()

        # Flag previous object as not current anymore
        if previous_object and not self.force_import:
            previous_object.current = False
            previous_object.add()


        package_dict, dcat_dict = self._get_package_dict(harvest_object)
        if not package_dict:
            return False


        if not package_dict.get('name'):
            package_dict['name'] = \
                self._get_package_name(harvest_object, package_dict['title_translated']['en'])

        # copy across resource ids from the existing dataset, otherwise they'll
        # be recreated with new ids

        if status == 'change':
            existing_dataset = self._get_existing_dataset(harvest_object.guid)
            if existing_dataset:
                copy_across_resource_ids(existing_dataset, package_dict)

        # Allow custom harvesters to modify the package dict before creating
        # or updating the package
        package_dict = self.modify_package_dict(package_dict,
                                                dcat_dict,
                                                harvest_object)
        # Unless already set by an extension, get the owner organization (if
        # any) from the harvest source dataset
        
        context = {
            'user': self._get_user_name(),
            'return_id_only': True,
            'ignore_auth': True,
        }
        '''
        ministries_list = logic.action.get.organization_list(context, {})
        ministries_show = []
        for ministry in ministries_list:
            ministries_show.append(logic.action.get.organization_show(context, {"id": ministry}))
        log.debug(ministries_show)
        # change organization title to bilingual
        ministry_results = list(filter(lambda x: x['title'] in package_dict['keywords']['en'], ministries_show))

        if len(ministry_results) > 0:
            package_dict['owner_org'] = ministry_results[0]["id"]
        if not package_dict.get('owner_org'):
            source_dataset = model.Package.get(harvest_object.source.id)
            if source_dataset.owner_org:
                package_dict['owner_org'] = source_dataset.owner_org
        '''
        # Flag this object as the current one
        harvest_object.current = True
        harvest_object.add()

        try:
            if status == 'new':
                package_schema = logic.schema.default_create_package_schema()
                context['schema'] = package_schema

                # We need to explicitly provide a package 

                package_dict['id'] = self.geohub_identifier_from_url(dcat_dict['identifier'])
                if 'extras' not in package_dict:
                    package_dict['extras'] = []    
                package_dict['extras'].append(
                    { 
                        "key": "guid",
                        "value": dcat_dict['identifier']
                    })
                package_schema['id'] = [unicode]

                # Save reference to the package on the object
                harvest_object.package_id = package_dict['id']
                harvest_object.add()

                # Defer constraints and flush so the dataset can be indexed with
                # the harvest object id (on the after_show hook from the harvester
                # plugin)
                model.Session.execute(
                    'SET CONSTRAINTS harvest_object_package_id_fkey DEFERRED')
                model.Session.flush()

            elif status == 'change':
                package_dict['id'] = harvest_object.package_id

            if status in ['new', 'change']:
                action = 'package_create' if status == 'new' else 'package_update'
                message_status = 'Created' if status == 'new' else 'Updated'

                package_id = p.toolkit.get_action(action)(context, package_dict)
                log.info('%s dataset with id %s', message_status, package_id)

        except Exception, e:
            dataset = json.loads(harvest_object.content)
            dataset_name = dataset.get('name', '')

            self._save_object_error('Error importing dataset %s: %r / %s' % (dataset_name, e, traceback.format_exc()), harvest_object, 'Import')
            return False

        finally:
            model.Session.commit()

        return True



def copy_across_resource_ids(existing_dataset, harvested_dataset):
    '''Compare the resources in a dataset existing in the CKAN database with
    the resources in a freshly harvested copy, and for any resources that are
    the same, copy the resource ID into the harvested_dataset dict.
    '''
    # take a copy of the existing_resources so we can remove them when they are
    # matched - we don't want to match them more than once.
    existing_resources_still_to_match = \
        [r for r in existing_dataset.get('resources')]

    # we match resources a number of ways. we'll compute an 'identity' of a
    # resource in both datasets and see if they match.
    # start with the surest way of identifying a resource, before reverting
    # to closest matches.
    resource_identity_functions = [
        lambda r: r['uri'],  # URI is best
        lambda r: (r['url'], r['title'], r['format']),
        lambda r: (r['url'], r['title']),
        lambda r: r['url'],  # same URL is fine if nothing else matches
    ]

    for resource_identity_function in resource_identity_functions:
        # calculate the identities of the existing_resources
        existing_resource_identities = {}
        for r in existing_resources_still_to_match:
            try:
                identity = resource_identity_function(r)
                existing_resource_identities[identity] = r
            except KeyError:
                pass

        # calculate the identities of the harvested_resources
        for resource in harvested_dataset.get('resources'):
            try:
                identity = resource_identity_function(resource)
            except KeyError:
                identity = None
            if identity and identity in existing_resource_identities:
                # we got a match with the existing_resources - copy the id
                matching_existing_resource = \
                    existing_resource_identities[identity]
                resource['id'] = matching_existing_resource['id']
                # make sure we don't match this existing_resource again
                del existing_resource_identities[identity]
                existing_resources_still_to_match.remove(
                    matching_existing_resource)
        if not existing_resources_still_to_match:
            break