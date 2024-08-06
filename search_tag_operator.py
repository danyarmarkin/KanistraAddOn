import bpy


class SearchTagOperator(bpy.types.Operator):
    bl_idname = "kanistra.search_tag_operator"
    bl_label = "View assets"
    bl_options = {"INTERNAL"}

    tag: bpy.props.StringProperty()

    def execute(self, context):
        if bpy.app.version_string >= "3.5.0":
            context.space_data.params.filter_search = self.tag
            context.space_data.params.catalog_id = ""
        else:
            if context.space_data.params.filter_search == self.tag:
                self.report({"INFO"}, "If no asset is shown, try selecting the 'ALL' catalog.")
            context.space_data.params.filter_search = self.tag
        return {"FINISHED"}
