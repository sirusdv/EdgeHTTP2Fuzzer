using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.IO;

using Peach.Core;
using Peach.Core.IO;
using Peach.Core.Dom;

namespace HPACK
{
    [Transformer("HuffmanTransformer", true)]
    [Serializable]
    public class HuffmanTransformer : Transformer
    {

        public HuffmanTransformer(DataElement parent, Dictionary<string, Variant> args) 
            : base(parent, args)
        {

        }
        protected override BitStream internalDecode(BitStream data)
        {

            byte[] buf = new byte[data.Length];
            data.Read(buf, 0, (int)data.Length);
            return new BitStream(Huffman.DECODER.Decode(buf));
        }

        protected override BitwiseStream internalEncode(BitwiseStream data)
        {
            byte[] buf = new byte[data.Length];
            data.Read(buf, 0, (int)data.Length);


            byte[] retbuf = new byte[Huffman.ENCODER.GetEncodedLength(buf)];
            MemoryStream ms = new MemoryStream(retbuf);
            using (BinaryWriter bw = new BinaryWriter(ms))
                Huffman.ENCODER.Encode(bw, buf);

            return new BitStream(retbuf);
        }
    }
}
