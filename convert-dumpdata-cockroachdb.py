import sys
import json

with open(f"{sys.argv[1]}.json") as f:
  data = json.load(f)

mapping = {}
curri = 0
def remapped(i, in_range):
  if i is None:
    return None
  i = int(i)
  if in_range and (i < 900000000000000000 or i > 1100000000000000000):
    print(i)
  global mapping, curri
  result = mapping.get(i)
  if result is None:
    result = curri
    mapping[i] = curri 
    curri += 1
  return result

def remap_field(obj, fi, in_range):
  if fi in obj:
    obj[fi] = remapped(obj[fi], in_range)

def remap_list(obj, fi, in_range):
  if fi in obj:
    obj[fi] = list(map(lambda x: remapped(x, in_range), obj[fi]))

def remap_named_list(obj, fi, in_range):
  if fi in obj:
    obj[fi] = list(map(lambda x: { "name": x["name"], "id": remapped(x["id"], in_range) }, obj[fi]))

# scheme = {}
# for item in data:
#   model_name = item["model"]
#   if item["model"] not in scheme:
#     scheme[model_name] = set()
#   for name, value in item["fields"].items():
#     try:
#       value = int(value)
#       if value > 900000000000000000 and value < 1100000000000000000:
#         scheme[model_name].add(name)
#     except:
#       pass
# print(scheme)

to_remap_fields = {
    'admin.logentry': {'content_type', 'user', 'object_id'}
  , 'auth.permission': {'content_type'}
  , 'auth.group': set()
  , 'contenttypes.contenttype': set()
  , 'sessions.session': set()
  , 'system.visualusergroup': set()
  , 'system.user': {'visual_group'}
  , 'system.usedtoken': set()
  , 'web.settings': {'site' , 'category'}
  , 'web.site': set()
  , 'web.tagscategory': set()
  , 'web.tag': {'category'}
  , 'web.category': set()
  , 'web.article': {'author' , 'parent'}
  , 'web.articleversion': {'article'}
  , 'web.articlelogentry': {'article' , 'user'}
  , 'web.vote': {'article', 'user', 'visual_group'}
  , 'web.externallink': set()
  , 'web.forumsection': set()
  , 'web.forumcategory': {'section'}
  , 'web.forumthread': {'article', 'category', 'author'}
  , 'web.forumpost': {'author', 'thread', 'reply_to'}
  , 'web.forumpostversion': {'author', 'post'}
  , 'web.file': {'article', 'deleted_by', 'author'}
  }
to_remap_lists = {
    'auth.group': { 'permissions' }
  , 'system.user': { 'groups', 'user_permissions' }
  , 'web.article': { 'tags' }
  }

for item in data:
  model_name = item["model"]
  in_range = model_name not in ["web.forumcategory", "web.forumpost", "web.forumpostversion", "web.forumthread"]
  if model_name != "sessions.session":
    remap_field(item, "pk", in_range)

  fields = item["fields"]

  if model_name == "web.articlelogentry":
    meta = fields["meta"]
    remap_field(meta, "id", True)
    remap_field(meta, "version_id", True)
    if "files" in meta:
      for filegroup_name in meta["files"]:
        remap_named_list(meta["files"], filegroup_name, True)
    if "tags" in meta:
      for filegroup_name in meta["tags"]:
        remap_list(meta["tags"], filegroup_name, True)
    if "source" in meta:
      remap_field(meta["source"], "version_id", True)
    remap_named_list(meta, "added_tags", True)
    remap_named_list(meta, "removed_tags", True)
    remap_field(meta, "parent_id", True)
    remap_field(meta, "prev_parent_id", True)
    if "votes" in meta:
      meta["votes"] = list(map(lambda x: { "date": x["date"], "user_id": remapped(x["user_id"], True), "visual_group_id": remapped(x["visual_group_id"], True), "vote": x["vote"] }, meta["votes"]))
    
  for field in to_remap_fields[model_name]:
    remap_field(fields, field, in_range)
  if model_name in to_remap_lists:
    for field in to_remap_lists[model_name]:
      remap_list(fields, field, in_range)
  item["model"] = item["model"].replace("system.", "web.")

with open(f"{sys.argv[1]}-out.json", "w") as f:
  json.dump(data, f, indent=2)
