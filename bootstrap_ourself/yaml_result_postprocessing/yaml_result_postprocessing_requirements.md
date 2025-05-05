# Requirements for YAML Result Postprocessing Task

To improve the quality and strictness of resulting yaml task and subtask file returned from AI, we will add a result postprocessing step before any verification or other existing use.

The postprocessing should be modular consisting of two major phases.

1. Scripted - containing a list of processing step with each step consisting of a python script taking the input yaml and a postprocessing result. The list will be processed in order passing the result of each stage to the next. When all stages have completed the original yaml will be replaced with the combined result. The goal of each step is to transform the yaml. Initially there should be one step which is the identity transform
2. AI improvements - this will be a dummy stage for now and will be in future implemented for now it should be an identity transform.
