# Work Zone Data Exchange (WZDx) Dashboard

According to the [specification](https://github.com/usdot-jpo-ode/wzdx), "the Work Zone Data Exchange (WZDx) Specification aims to make harmonized work zone data provided by infrastructure owners and operators (IOOs) available for third party use, making travel on public roads safer and more efficient through ubiquitous access to data on work zone activity." More information on this project can be found on the [project's homepage](https://www.transportation.gov/av/data/wzdx).

At the time of writing, 25 different organizations provide data feeds that align with various versions of the specification, which can be viewed publicly on the [U.S. DOT's public data portal](https://data.transportation.gov/Roadways-and-Bridges/Work-Zone-Data-Exchange-WZDx-Feed-Registry/69qe-yiui/data_preview). These feeds are archived regularly at the [ITS Work Zone Sandbox](https://usdot-its-workzone-publicdata.s3.amazonaws.com/index.html), but there is currently no mechanism in place for Volpe team members to regularly ensure data validity, accuracy, freshness, or alignment with the specification.

This project aims to address this by creating an internal dashboard that will regularly query the public data hub for all available feeds and their metadata, validate individual feeds, and alert Volpe WZDx team members whenever an error or warning is found.

## Suport
For support, please contact [diego.temkin@dot.gov](mailto:diego.temkin@dot.gov) or [avdx@dot.gov](mailto:avdx@dot.gov).

## License
The WZDx Dashboard project is in the worldwide public domain (i.e., in the public domain within the United States - copyright and related rights in the work worldwide are waived through the [CC0 1.0 Universal](https://creativecommons.org/share-your-work/public-domain/cc0/) public domain dedication). All contributions to this project will be released under the CC0 dedication. By submitting a pull request, you are agreeing to comply with the waiver of copyright interest. see [License](./LICENSE) for more details.
