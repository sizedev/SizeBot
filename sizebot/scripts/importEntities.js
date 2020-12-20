function importEntities() {
    model_heights = {}
    Object.values(availableEntitiesByName)
        .map(e => e.constructor())
        .forEach(function(entity) {
            model_heights[entity.name] = {};
            Object.entries(entity.views)
                .forEach(function([name, view]) {
                    model_heights[entity.name][name] = view.attributes.height.base.toNumber("meters");
                });
        });
    return JSON.stringify(model_heights, null, 4);
}
importEntities()