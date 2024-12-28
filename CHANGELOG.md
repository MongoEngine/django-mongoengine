# Changelog

All notable changes to this project will be documented in this file. See [standard-version](https://github.com/conventional-changelog/standard-version) for commit guidelines.

## [0.6.0-beta.3](https://github.com/MongoEngine/django-mongoengine/compare/v0.6.0-beta.2...v0.6.0-beta.3) (2024-12-28)


### Bug Fixes

* Drop pypy 3.9 support ([cf5a89b](https://github.com/MongoEngine/django-mongoengine/commit/cf5a89bd0953091e9028cf18496c977ebe7e4145))

## [0.6.0-beta.2](https://github.com/MongoEngine/django-mongoengine/compare/v0.6.0-beta.1...v0.6.0-beta.2) (2023-11-16)


### Bug Fixes

* Fix BooleanField ([e5a87c6](https://github.com/MongoEngine/django-mongoengine/commit/e5a87c6ed7b23018410903524915ad7a0e182ead))

## [0.6.0-beta.1](https://github.com/MongoEngine/django-mongoengine/compare/v0.6.0-beta.0...v0.6.0-beta.1) (2023-11-16)


### Features

* Switch to ruff formatter ([3183d28](https://github.com/MongoEngine/django-mongoengine/commit/3183d286f152d418acf49ecee8b3c3dc49d6b53c))

## [0.6.0-beta.0](https://github.com/MongoEngine/django-mongoengine/compare/v0.5.7-beta.1...v0.6.0-beta.0) (2023-11-15)


### ⚠ BREAKING CHANGES

* Removed `blank` argument support for fields, use mongoengine `required` instead.
  `ast-grep` can be used to automatically rewrite old code:

  ```
  ast-grep scan -r sg-rules/0.6.0-rewrite-blank.yml . -i
  ```
  Be careful to review, clean it up and test.

* Switch to mongoengine style field arguments. Drop old django ([#200](https://github.com/MongoEngine/django-mongoengine/issues/200)) ([9d56f6a](https://github.com/MongoEngine/django-mongoengine/commit/9d56f6a58ccee93e2acae7af0a8d81d9aa43ae5b))

### [0.5.7-beta.1](https://github.com/MongoEngine/django-mongoengine/compare/v0.5.7-beta.0...v0.5.7-beta.1) (2023-11-04)


### Bug Fixes

* Fix typing_extensions dependency ([6fa3394](https://github.com/MongoEngine/django-mongoengine/commit/6fa339407c32ae4b49589d9f5f1b1628c7458cf7))

### [0.5.7-beta.0](https://github.com/MongoEngine/django-mongoengine/compare/v0.5.6...v0.5.7-beta.0) (2023-11-04)


### Bug Fixes

* More work on typing support; add black and ruff ([b9a0e0e](https://github.com/MongoEngine/django-mongoengine/commit/b9a0e0ec420faaec30a3d6a2f37d53ecf5461c6e))

### [0.5.6](https://github.com/MongoEngine/django-mongoengine/compare/v0.5.6-beta.0...v0.5.6) (2023-11-03)


### Bug Fixes

* **typing:** Add static types for dynamic classes ([5c843e6](https://github.com/MongoEngine/django-mongoengine/commit/5c843e60f6cd26ebc232dac66b56c626a5808e73))

### [0.5.6-beta.0](https://github.com/MongoEngine/django-mongoengine/compare/v0.5.5...v0.5.6-beta.0) (2023-08-16)


### Features

* Update test matrix; drop python 3.7 ([1bca66a](https://github.com/MongoEngine/django-mongoengine/commit/1bca66ad9238420790077c025424ff6c42cb61cb))


### Bug Fixes

* Fix queryset comparison for django 4.2 ([da5f2b5](https://github.com/MongoEngine/django-mongoengine/commit/da5f2b5aab6a850a8217284bf6d24235db847edc))

### [0.5.5](https://github.com/MongoEngine/django-mongoengine/compare/v0.5.4...v0.5.5) (2023-08-10)


### Bug Fixes

* **admin:** Use page_num without +1 (just like django does) ([#186](https://github.com/MongoEngine/django-mongoengine/issues/186)) ([8377bff](https://github.com/MongoEngine/django-mongoengine/commit/8377bff9126fb9a8409064e8ff0d87072ae6cb10))

### [0.5.4](https://github.com/MongoEngine/django-mongoengine/compare/v0.5.3...v0.5.4) (2022-05-27)


### Bug Fixes

* Fix package metadata ([a2496b4](https://github.com/MongoEngine/django-mongoengine/commit/a2496b4854d67f843f1aae5e9ae0c36bf67a3c74))

### [0.5.3](https://github.com/MongoEngine/django-mongoengine/compare/v0.5.2...v0.5.3) (2022-05-27)


### Bug Fixes

* Properly set attributes for auto created field ([3b9c039](https://github.com/MongoEngine/django-mongoengine/commit/3b9c039791991be2b01693c9c561fbcd82ad7564))

### [0.5.2](https://github.com/MongoEngine/django-mongoengine/compare/v0.5.1...v0.5.2) (2022-05-26)


### Bug Fixes

* Fix create without id ([41bc837](https://github.com/MongoEngine/django-mongoengine/commit/41bc837916fca5f8226b4c1b0491db8766477f1f))

### [0.5.1](https://github.com/MongoEngine/django-mongoengine/compare/v0.5.0...v0.5.1) (2022-05-26)


### Bug Fixes

* Add placeholders for get_path_to_parent/get_path_from_parent ([3653d21](https://github.com/MongoEngine/django-mongoengine/commit/3653d21b979d351b3dd411dbcd74d55e331fbddf))
* Use django-patched ObjectIdField for auto created primary keys. ([5fde4a6](https://github.com/MongoEngine/django-mongoengine/commit/5fde4a6e17d11cab1e53d32a00b15b3ac55ef209))

## [0.5.0](https://github.com/MongoEngine/django-mongoengine/compare/v0.4.5...v0.5.0) (2022-05-14)


### Features

* Clean up deprecated code for django-4 ([c82cbc6](https://github.com/MongoEngine/django-mongoengine/commit/c82cbc641a78c59e46b5b0e7be0e2867260e17c0)), closes [#156](https://github.com/MongoEngine/django-mongoengine/issues/156)
* Drop django 2.2, add django 4.0 ([6c3d068](https://github.com/MongoEngine/django-mongoengine/commit/6c3d068b305a8f0ba88597ddeb97281a31f204fe))


### Bug Fixes

* Fix 'StringField' object has no attribute 'flatchoices' ([#161](https://github.com/MongoEngine/django-mongoengine/issues/161)) ([db3860d](https://github.com/MongoEngine/django-mongoengine/commit/db3860d39fa29819fde71953e905f117f680a3be))
* Fix invalid import EMPTY_CHANGELIST_VALUE in django >= 3 ([e8a75e8](https://github.com/MongoEngine/django-mongoengine/commit/e8a75e8e5860545ecfbadaf1b1285495022bd7cb))
* **deps:** Move pytests dependency int dev-dependencies ([f7e37a7](https://github.com/MongoEngine/django-mongoengine/commit/f7e37a75e6612a4243ccc9abdb22f2dc72f53d9e))

### [0.4.6](https://github.com/MongoEngine/django-mongoengine/compare/v0.4.5...v0.4.6) (2021-04-11)


### Bug Fixes

* **deps:** Move pytests dependency int dev-dependencies ([f7e37a7](https://github.com/MongoEngine/django-mongoengine/commit/f7e37a75e6612a4243ccc9abdb22f2dc72f53d9e))

### [0.4.5](https://github.com/MongoEngine/django-mongoengine/compare/v0.4.5-beta.4...v0.4.5) (2021-04-11)


### Features

* Remove six ([773c791](https://github.com/MongoEngine/django-mongoengine/commit/773c79169b08ccd71f958e1855a2c47b1c7ebb7e))
* **drf-spectacular:** AutoSchema generator for drf-spectacular support. ([2ef9529](https://github.com/MongoEngine/django-mongoengine/commit/2ef9529e330d482957acf582a56ac7aeabe853c6))
* Support Django 3.2

### Bug Fixes

* Add missing __init__.py ([bb11d36](https://github.com/MongoEngine/django-mongoengine/commit/bb11d36cf754bfd19bcff1e643fabd28c44f9e38))


### 2016-01-27

* Support for django 1.9, minimum django version: 1.7
* Moved `django_mongoengine.mongo_auth.MongoUser` to `django_mongoengine.mongo_auth.models.MongoUser`
