"""Final static check on the repack: does every material in every repacked bundle now
point at a shader that actually exists in the live game, through an external that
names the live shaders bundle?

This is the strongest claim available without running the client.

Usage: python verify_repack.py <repacked-root> <shaders-bundle>
"""
import sys
import os
import collections

import UnityPy


def main(root, shaders):
    print("indexing live shaders ...", flush=True)
    env = UnityPy.load(shaders)
    valid = set()
    cab = None
    for name, reader in env.files.items():
        inner = getattr(reader, "files", None)
        if isinstance(inner, dict):
            for fname in inner:
                if not fname.endswith(".resS"):
                    cab = fname
    for obj in env.objects:
        if obj.type.name == "Shader":
            valid.add(obj.path_id)
    print(f"  {len(valid)} shaders, CAB={cab}\n", flush=True)
    want_ext = f"archive:/{cab}/{cab}"

    ok = bad = selfok = 0
    bad_detail = collections.Counter()
    files = 0
    for dp, _d, fs in os.walk(root):
        for f in sorted(fs):
            if not f.endswith(".bundle"):
                continue
            p = os.path.join(dp, f)
            files += 1
            try:
                e = UnityPy.load(p)
            except Exception as ex:
                bad += 1
                bad_detail[f"unloadable: {type(ex).__name__}"] += 1
                continue

            ext = []
            for reader in e.files.values():
                inner = getattr(reader, "files", None)
                if isinstance(inner, dict):
                    for sf in inner.values():
                        if hasattr(sf, "externals"):
                            ext = [x.path for x in sf.externals]
                            break
                if ext:
                    break

            # fileID == 0 means "the shader is an object in *this* bundle", which is legal and
            # is not a dangling reference. Four HATS/ARMYCAP materials do this, pointing at a
            # Unity `Standard` shader compiled into the bundle itself. Do not treat fid == 0 as
            # out of range -- an earlier version of this script did, and reported four healthy
            # materials as broken. But do not wave them through either: check the pathID really
            # is a Shader in this bundle.
            own_shaders = {o.path_id for o in e.objects if o.type.name == "Shader"}

            for obj in e.objects:
                if obj.type.name != "Material":
                    continue
                try:
                    d = obj.read()
                except Exception:
                    continue
                sh = getattr(d, "m_Shader", None)
                if sh is None:
                    continue
                mat = getattr(d, "m_Name", "?")
                fid = sh.m_FileID
                if fid == 0:
                    if sh.m_PathID in own_shaders:
                        selfok += 1
                    else:
                        bad += 1
                        bad_detail["in-bundle shader pathID does not exist"] += 1
                        print(f"   {os.path.relpath(p, root)} :: {mat} -> in-bundle {sh.m_PathID}")
                    continue
                if not (1 <= fid <= len(ext)):
                    bad += 1
                    bad_detail["fileID out of range"] += 1
                    continue
                if ext[fid - 1] != want_ext:
                    bad += 1
                    bad_detail["external is not the live shaders bundle"] += 1
                    print(f"   {os.path.relpath(p, root)} :: {mat} -> {ext[fid-1]}")
                    continue
                if sh.m_PathID not in valid:
                    bad += 1
                    bad_detail["shader pathID not in live shaders"] += 1
                    print(f"   {os.path.relpath(p, root)} :: {mat} -> pathID {sh.m_PathID}")
                    continue
                ok += 1

    print(f"\nbundles checked : {files}")
    print(f"materials resolving to a live shader : {ok}")
    print(f"materials resolving in-bundle        : {selfok}")
    print(f"materials still broken               : {bad}")
    for k, v in bad_detail.most_common():
        print(f"    {k}: {v}")
    print(f"total materials                      : {ok + selfok + bad}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
