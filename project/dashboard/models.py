from django.db import models

# Create your models here.


class Feed(models.Model):
    """
    A model representing the information available at https://data.transportation.gov/d/69qe-yiui/. To be updated regularly via crontab.
    """

    # The following fields are all from the public data hub, https://data.transportation.gov/d/69qe-yiui
    state = models.TextField("State")
    issuingorganization = models.TextField("Issuing Organization")
    feedname = models.TextField("Feed Name", primary_key=True)
    url = models.URLField("URL")
    format = models.TextField("Format")
    active = models.BooleanField("Active")
    datafeed_frequency_update = models.TextField("Datafeed Update Frequency")
    version = models.TextField("Version")
    sdate = models.DateTimeField("Start Date")
    edate = models.DateTimeField("End Date", null=True)
    needapikey = models.BooleanField("Need API Key")
    apikeyurl = models.URLField("API key URL", null=True)
    pipedtosandbox = models.BooleanField("Piped to Sandbox")
    lastingestedtosandbox = models.DateTimeField(
        "Last Ingested To Sandbox (UTC)", null=True
    )
    pipedtosocrata = models.BooleanField("Piped to Socrata")
    socratadatasetid = models.TextField("Socrata Dataset ID", null=True)
    geocoded_column = models.JSONField(
        "State Coordinate"
    )  # Change to field time once GeoDjango is set up

    # The following fields are needed for data processing
    last_checked = models.DateTimeField("Last Updated", auto_now=True)
    feed_data = models.JSONField("Feed Data")

    def __str__(self):
        return self.feedname


class FeedError(models.Model):
    feed = models.ForeignKey(Feed, on_delete=models.CASCADE)
    error_message = models.TextField()
    datetime_found = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.error_message


class APIKey(models.Model):
    feed = models.OneToOneField(Feed, on_delete=models.CASCADE, primary_key=True)
    key = models.TextField()

    def __str__(self):
        return self.key


# Upload class from ReVal. TODO: Modify to fit WZDx use case
# class Upload(models.Model):
#     """
#     An abstract model intended to be subclassed by the project
#     to further define the Upload object.

#     Tracks state and history of the upload
#     and who has modified it at each step.

#     Also can resolve duplicate file issues,
#     if `unique_metadata_fields` is defined in the project.
#     """

#     class Meta:
#         abstract = True

#     STATUS_CHOICES = (
#         ("LOADING", "Loading"),
#         ("PENDING", "Pending"),
#         ("STAGED", "Staged"),
#         ("INSERTED", "Inserted"),
#         ("DELETED", "Deleted"),
#     )

#     submitter = models.ForeignKey(User, on_delete=models.CASCADE)
#     created_at = models.DateTimeField(auto_now_add=True)
#     file_metadata = models.JSONField(null=True)
#     file = models.FileField()
#     raw = models.BinaryField(null=True)
#     validation_results = models.JSONField(null=True)
#     status = models.CharField(
#         max_length=10,
#         choices=STATUS_CHOICES,
#         default="LOADING",
#     )
#     updated_at = models.DateTimeField(auto_now=True)
#     status_changed_by = models.ForeignKey(
#         User, related_name="+", null=True, on_delete=models.CASCADE
#     )
#     status_changed_at = models.DateTimeField(null=True)
#     replaces = models.ForeignKey(
#         "self", null=True, related_name="replaced_by", on_delete=models.CASCADE
#     )

#     unique_metadata_fields = []

#     def duplicate_of(self):
#         """
#         We are assuming there won't be *multiple* duplicates.

#         This is far less efficient than using a database unique index,
#         but we want to leave file_metadata very flexibly defined.
#         """
#         if self.unique_metadata_fields:
#             duplicates = self.__class__.objects
#             for field in self.unique_metadata_fields:
#                 duplicates = duplicates.filter(
#                     **{"file_metadata__" + field: self.file_metadata[field]}
#                 )
#             # Silently delete abandoned in-process duplicates
#             duplicates.filter(status="LOADING").exclude(id=self.id).delete()
#             return duplicates.exclude(status="DELETED").exclude(id=self.id).first()
#         return None

#     @property
#     def file_type(self):
#         (root, ext) = os.path.splitext(self.file.name)
#         return ext.lower()[1:]

#     def file_metadata_as_params(self):
#         if self.file_metadata:
#             return urlencode(self.file_metadata)
#         else:
#             return ""

#     def descriptive_fields(self):
#         return self.file_metadata or {"file_name": self.file.name}
