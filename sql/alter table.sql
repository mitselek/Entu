/* 2012-08-19 12:59 Add javascript datatype to property definition */
ALTER TABLE `property_definition` CHANGE `datatype` `datatype` ENUM('boolean','counter','counter_value','decimal','date','datetime','file','integer','reference','string','text','javascript')  NOT NULL  DEFAULT 'string';
