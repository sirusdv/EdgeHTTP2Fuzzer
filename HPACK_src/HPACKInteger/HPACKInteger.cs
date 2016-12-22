using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

using Peach.Core;
using Peach.Core.Analyzers;
using Peach.Core.Dom;
using Peach.Core.IO;

using ValueType = Peach.Core.Dom.ValueType;
using Peach.Core.Cracker;
using System.IO;
using System.Xml;

namespace HPACK
{

    [DataElement("HPACKInteger", DataElementTypes.NonDataElements)]
    [PitParsable("HPACKInteger")]
    [Parameter("name", typeof(string), "Element name", "")]
    [Parameter("length", typeof(uint?), "Length in data element", "")]
    [Parameter("lengthType", typeof(LengthType), "Units of the length attribute", "bytes")]
    [Parameter("value", typeof(int), "Default value", "0")]
    [Parameter("valueType", typeof(ValueType), "Format of value attribute", "string")]
    [Parameter("mutable", typeof(bool), "Is element mutable", "true")]
    [Parameter("constraint", typeof(string), "Scripting expression that evaluates to true or false", "")]
    [Parameter("minOccurs", typeof(int), "Minimum occurances", "1")]
    [Parameter("maxOccurs", typeof(int), "Maximum occurances", "1")]
    [Parameter("occurs", typeof(int), "Actual occurances", "1")]
    [Parameter("prefixBits", typeof(int), "Number of HPACK prefix bits.", "1")]
    [Serializable]
    public class HPACKInteger : Number
    {
        public int prefixBits { get; set; }


        public HPACKInteger()
        {
            lengthType = LengthType.Bits;
            length = 64;
            Signed = false;
            LittleEndian = true;
            DefaultValue = new Variant(0);

        }
        public HPACKInteger(string name)
            : base(name)
        {
            lengthType = LengthType.Bits;
            length = 64;
            Signed = false;
            LittleEndian = true;
            DefaultValue = new Variant(0);
        }


        public static new DataElement PitParser(PitParser context, XmlNode node, DataElementContainer parent)
        {
            var ret = Generate<HPACKInteger>(node, parent);


            ret.prefixBits = node.getAttrInt("prefixBits");

            context.handleCommonDataElementAttributes(node, ret);
            context.handleCommonDataElementChildren(node, ret);
            context.handleCommonDataElementValue(node, ret);

            return ret;
        }

        public override bool hasLength { get { return false; } }
        public override bool isDeterministic { get { return true; } }

        protected override Variant GetDefaultValue(BitStream data, long? size)
        {

            int val = 0;

            int max_number = (1 << prefixBits) - 1;
            int mask = 0xFF >> (8 - prefixBits);

            int index = 0;
            ulong uread = 0;
            if (data.ReadBits(out uread, prefixBits) != prefixBits)
                throw new SoftException("Out of bits.");

            int read = (int)(uread);

            val = read & mask;
            if (val == max_number)
            {
                for (;;)
                {
                    index++;
                    int next = data.ReadByte();
                    if (read == -1)
                        throw new SoftException("Out of bytes");

                    if (next >= 128)
                        val += (next - 128) * ((int)Math.Pow(128, index - 1));
                    else
                    {
                        val += next * ((int)Math.Pow(128, index - 1));
                        break;
                    }
                }
            }

            return new Variant(val);
        }

        protected override BitwiseStream InternalValueToBitStream()
        {

            var val = (ulong)InternalValue;
            var ret = new BitStream();

            ulong max_number = (ulong)((1 << prefixBits) - 1);

            if (val < max_number)
            {
                ret.WriteByte((byte)val);
            }
            else
            {
                ret.WriteByte((byte)max_number);

                val -= max_number;

                while (val >= 128)
                {
                    ret.WriteByte((byte)((val % 128) + 128));
                    val /= 128;
                }
                ret.WriteByte((byte)val);
            }

            ret.SeekBits(8 - prefixBits, SeekOrigin.Begin);

            var ret2 = new BitStream();
            ret.CopyTo(ret2);
            ret2.Seek(0, SeekOrigin.Begin);
            return ret2;
        }

    }
}
