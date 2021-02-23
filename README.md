# Rasa V2使用BERT中文语言模型

Rasa支持使用HuggingFace Transformers对接现成的语言模型，目测只要是支持masked-lm功能的模型都可以用。

只需要正确配置 `LanguageModelFeaturizer` 即可。

当前遇到的问题是 `LanguageModelTokenizer` 是deprecated状态，并且此tokenizer不支持设置 `language: zh` ，但是 `LanguageModelFeaturizer` 必须前置一个tokenizer。

当前使用的是[howl-anderson/rasa_chinese_service/lm_tokenizer](https://github.com/howl-anderson/rasa_chinese_service/pull/1)封装的一个HTTP服务作为Tokenizer。

# `LanguageModelFeaturizer` 使用PyTorch模型

当前 `LanguageModelFeaturizer` 默认使用TF Keras模型 (`.h5` 格式)，如果需要使用PyTorch的模型的话，需要fork `rasa/nlu/featurizers/dense_featurizer/lm_featurizer.py` 并做[如下修改](https://github.com/lhr0909/rasa-v2-nlu-bert-chinese/commit/2a431adde81095f705858925b02ecf07a932fda4)

以 [Bert-Chinese-WWM模型](https://github.com/ymcui/Chinese-BERT-wwm)为例，下载PyTorch模型之后放到一个目录下（如 `./bert-models/chinese_wwm_ext_pytorch`），把 `bert_config.json` 重命名成 `config.json` 然后做如下配置即可：

```yaml
  - name: "components.lm_featurizer.LanguageModelFeaturizer"
    model_name: "bert"
    # model_weights: "bert-base-chinese"
    model_weights: "./bert-models/chinese_wwm_ext_pytorch"
    from_pt: true
    cache_dir: "./cache
```