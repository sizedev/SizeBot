function importEntities() {
    model_heights = {}
    Object.values(availableEntitiesByName)
        .map(e => e.constructor())
        .forEach(function(entity) {
            model_heights[entity.name] = {};
            Object.values(entity.views)
                .forEach(function(view) {
                    model_heights[entity.name][view.name] = view.height.toNumber("meters");
                });
        });
    return JSON.stringify(model_heights, null, 4);
}
importEntities()
