The workflow **test.cwl** tests all features of morph-tool, unless compare-folder, with 2 different files
- **2013_03_06_cell08_876_H41_05_Cell2.ASC** ([DOI](https://doi.org/10.25493/HW89-4SD))
- **2013_03_06_cell11_1125_H41_06.ASC** ([DOI](https://doi.org/10.25493/D9AF-Z08))

To test the file difference you can run:

```
cwltool test.cwl test-different.yaml
```

This test should return an error that is expected, Morph-Tool returns an failure exit code when the 2 compared morphologies are different.

This test is passed when the same files are compared :

```
cwltool test.cwl test-same.yaml
```

that compares the same files together.

The feature **simplify** uses a deprecated test on arrays, that raises an error for Python > 3.9.

